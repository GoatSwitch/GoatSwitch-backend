import json
import logging
import os
import time
from dataclasses import asdict, dataclass

from gs_common.CodeProject import CodeProject
from signalrcore.hub_connection_builder import HubConnectionBuilder


@dataclass
class GSClientResult:
    trace_id: str = None
    runtime: float = None
    timeout: bool = False
    connected: bool = False
    generate_unittests_state: str = "default"
    translate_state: str = "default"
    validate_state: str = "default"
    generate_unittests_error: str = None
    translate_error: str = None
    validate_error: str = None

    def toDict(self):
        return asdict(self)

    @staticmethod
    def fromString(s: str):
        res_dict: dict = json.loads(s)
        if not isinstance(res_dict, dict):
            raise Exception(f"Invalid string to parse: {s}")
        res = GSClientResult()
        for key in res.__dict__.keys():
            if key in res_dict:
                setattr(res, key, res_dict[key])
        return res


class GSClient:
    def __init__(self, server_url, max_wait_time, project_name, run_id="") -> None:
        self.server_url = server_url
        self.run_id = run_id
        self.max_wait_time = max_wait_time
        self.project_name = project_name

        # concat run_id to the api key to aggregate the logs later
        GS_API_KEY = os.getenv("GS_API_KEY")
        self.access_token = GS_API_KEY + run_id

        self.hub_connection = None

        self.result = GSClientResult()
        self.log_terminal_errors: list[str] = []
        # Results is a list of [result, log_level]
        # list[dict[str, str], str]
        # keys: "solution", "test_output", "error", "return_code"
        self.ut_result: list[dict, str] = []
        # list[dict[str, str], str]
        # keys: "solutions", "error"
        self.tl_candidates: list[dict, str] = []
        # list[dict[str, str], str]
        # keys: "solution", "test_output", "error", "return_code"
        self.ut_candidates: list[list, str] = []
        # same as tl_candidates
        self.assessment_result: list[dict, str] = []
        self.tl_result: list[dict, str] = []
        # NOTE: ut_candidates has different struct...
        # list[list[CodeProject], str
        self.plan: str = ""

    def connect(self):
        self.hub_connection = (
            HubConnectionBuilder()
            .with_url(
                f"{self.server_url}/frontendhub?access_token={self.access_token}",
                options={"verify_ssl": True},
            )
            .configure_logging(logging.INFO)
            .with_automatic_reconnect(
                {
                    "type": "raw",
                    "keep_alive_interval": self.max_wait_time,
                    "reconnect_interval": 5,
                    "max_attempts": 5,
                }
            )
            .build()
        )

        def on_connect():
            logging.info(f"GSClient {self.project_name}: Connection started")

        def on_close():
            logging.info(f"GSClient {self.project_name}: Connection closed")
            self.result.connected = False

        def on_message(msg):
            logging.info(f"GSClient {self.project_name}: Message received: {msg}")

        def on_return_gen_plan(message):
            logging.info(f"GSClient {self.project_name}: Return gen plan: {message}")
            self.plan = message[0]

        def on_log_logs(msg: list[str, str]):
            msg_text, msg_log_level = msg
            if msg_log_level == "error":
                self.log_terminal_errors.append(msg_text)
                if "Unexpected error occurred" in msg_text:
                    self.result.validate_error = msg_text
                    self.result.validate_state = "error"
                    self.result.timeout = True
                if "PLANGEN" in msg_text:
                    self.result.translate_error = msg_text
                    self.result.translate_state = "error"
                if "TLGEN" in msg_text:
                    self.result.translate_error = msg_text
                    self.result.translate_state = "error"
                if "UTGEN" in msg_text:
                    self.result.generate_unittests_error = msg_text
                    self.result.generate_unittests_state = "error"
                if "some steps failed" in msg_text:
                    self.result.validate_error = msg_text
                    self.result.validate_state = "error"

            if "Trace ID:" in msg_text:
                self.result.trace_id = msg_text.split("Trace ID:")[1].strip()

            # NOTE: for pickers, the error is in ut/tl_result
            # if "Picking translation failed" in msg_text:
            #     self.result.validate_error = msg_text
            #     self.result.validate_state = "error"
            # if "Picking unit tests failed" in msg_text:
            #     self.result.generate_unittests_error = msg_text
            #     self.result.generate_unittests_state = "error"

            logging.info(f"GSClient {self.project_name}: Log logs: {msg}")

        def on_update_progress(msg):
            logging.info(f"GSClient {self.project_name}: Update progress: {msg}")
            # update the state
            if msg[0]["key"] == "generate_unittests":
                self.result.generate_unittests_state = msg[0]["progress_state"]
            if msg[0]["key"] == "translate":
                self.result.translate_state = msg[0]["progress_state"]
            if msg[0]["key"] == "validate":
                self.result.validate_state = msg[0]["progress_state"]

        def on_error(msg):
            logging.info(f"GSClient {self.project_name}: Error: {msg}")

        def on_log_ut(msg):
            logging.info(f"GSClient {self.project_name}: Received UT candidates")
            self.ut_candidates = msg

        def on_log_ut_result(msg):
            logging.info(f"GSClient {self.project_name}: Received UT result")
            self.ut_result = msg
            if self.ut_result[1] == "error":
                self.result.generate_unittests_state = "error"
                self.result.generate_unittests_error = self.ut_result[0]["error"]

        def on_log_tl_candidates(msg):
            logging.info(
                f"GSClient {self.project_name}: Received translation candidates"
            )
            self.tl_candidates = msg

        def on_log_tl_result(msg):
            logging.info(f"GSClient {self.project_name}: Received translation result")
            self.tl_result = msg
            if self.tl_result[1] == "error":
                self.result.translate_state = "error"
                self.result.translate_error = self.tl_result[0]["error"]

        def on_log_assessment_result(msg):
            logging.info(f"GSClient {self.project_name}: Received assessment result")
            self.assessment_result = msg

        # register callbacks
        self.hub_connection.on_open(on_connect)
        self.hub_connection.on_close(on_close)
        self.hub_connection.on_error(on_error)
        self.hub_connection.on("returnWorkflowGenPlanAsync", on_return_gen_plan)
        self.hub_connection.on("logLogs", on_log_logs)
        self.hub_connection.on("logUT", on_log_ut)
        self.hub_connection.on("logUTResult", on_log_ut_result)
        self.hub_connection.on("logTranslationCandidates", on_log_tl_candidates)
        self.hub_connection.on("logTranslationResult", on_log_tl_result)
        self.hub_connection.on("logAssessmentResult", on_log_assessment_result)
        self.hub_connection.on("message", on_message)
        self.hub_connection.on("updateProgress", on_update_progress)

        self.hub_connection.start()
        # wait 1 sec for connection to establish
        time.sleep(1)

    def send_workflow_basic(
        self,
        source_project: CodeProject,
        target_language: str,
    ):
        self.hub_connection.send(
            "WorkflowBasicAsync", [source_project, target_language]
        )
        return self.wait_for_result()

    def send_workflow_gen_plan(
        self,
        source_project: CodeProject,
        instruction: str,
    ):
        self.hub_connection.send("WorkflowGenPlanAsync", [source_project, instruction])
        self.wait_for_result()
        return self.plan

    def send_workflow_execute_plan(
        self,
        source_project: CodeProject,
        instruction: str,
    ):
        self.hub_connection.send(
            "WorkflowExecutePlanAsync", [source_project, instruction]
        )
        return self.wait_for_result()

    def send_workflow_generate_tests(
        self,
        source_project: CodeProject,
        instruction: str = "",
        test_project: CodeProject = None,
    ):
        if test_project is None:
            test_project = CodeProject()
        self.hub_connection.send(
            "WorkflowGenerateTestsAsync", [source_project, instruction, test_project]
        )
        # set TL to error because we don't want to do TLPicker
        time.sleep(1)
        self.result.translate_state = "error"
        return self.wait_for_result()

    def send_workflow_given_candidates(
        self,
        source_project: CodeProject,
        test_projects: list[CodeProject],
        translated_projects: list[CodeProject],
        target_language: str,
    ):
        self.hub_connection.send(
            "WorkflowGivenCandidatesAsync",
            [source_project, test_projects, translated_projects, target_language],
        )
        # set TL to completed because we already have the candidates
        time.sleep(1)
        self.result.translate_state = "completed"
        return self.wait_for_result()

    def send_workflow_improve_translation(
        self,
        source_project: CodeProject,
        test_project: CodeProject,
        translated_project: CodeProject,
        instruction: str,
        target_language: str,
    ):
        self.hub_connection.send(
            "WorkflowImproveTranslationAsync",
            [
                source_project,
                test_project,
                translated_project,
                instruction,
                target_language,
            ],
        )
        return self.wait_for_result()

    def wait_for_result(self) -> GSClientResult:
        self.result.connected = True
        start_time = time.time()
        log_timer = time.time()
        while True:
            # stop if timeout
            if time.time() - start_time > self.max_wait_time:
                logging.info(f"Timeout for repo {self.project_name}")
                self.result.timeout = True
                break
            # stop if closed or disconnected
            if not self.result.connected:
                logging.info(f"Connection closed for repo {self.project_name}")
                break
            # stop if validate completed
            if self.result.validate_state == "completed":
                logging.info(f"Validation completed for repo {self.project_name}")
                break
            # stop if validate error
            if self.result.validate_state == "error":
                logging.info(f"Validation error for repo {self.project_name}")
                break
            # stop if both translate and generate_unittests are in error
            if (
                self.result.generate_unittests_state == "error"
                and self.result.translate_state == "error"
            ):
                logging.info(
                    f"Translate and generate_unittests are in error for repo {self.project_name}"
                )
                break
            # stop if translate completed and generate_unittests is in error
            if (
                self.result.generate_unittests_state == "error"
                and self.result.translate_state == "completed"
            ):
                logging.info(
                    f"Translate completed but generate_unittests is in error for repo {self.project_name}"
                )
                break
            # stop if generate_unittests completed and translate is in error
            if (
                self.result.generate_unittests_state == "completed"
                and self.result.translate_state == "error"
            ):
                logging.info(
                    f"Generate_unittests completed but translate is in error for repo {self.project_name}"
                )
                break

            time.sleep(2)
            if time.time() - log_timer < 10:
                continue

            log_timer = time.time()
            str_waiting = "Waiting... Status: "
            str_waiting += (
                f"generate_unittests: {self.result.generate_unittests_state}, "
            )
            str_waiting += f"translate: {self.result.translate_state}, "
            str_waiting += f"validate: {self.result.validate_state}"
            logging.info(str_waiting)

        self.result.runtime = round(time.time() - start_time, 2)
        logging.info(
            f"Total runtime for repo {self.project_name}: {self.result.runtime}"
        )
        # wait for some more signalr messages for race conditions
        time.sleep(2)
        return self.result

    def disconnect(self):
        self.hub_connection.stop()

    def get_result(self) -> GSClientResult:
        return self.result
