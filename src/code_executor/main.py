import json
import logging
import os
import shutil
import threading

import yaml
from dapr.ext.grpc import App, InvokeMethodRequest, InvokeMethodResponse
from gs_common import setup_logging, timed
from gs_common.CodeProject import CodeProject, ExecutionResult
from gs_common.file_ops import (
    generate_save_dir,
)
from gs_common.tracing import extract_trace_info

from src.code_executor.factories import CodeExecutorFactory
from src.code_executor.pre_migration_assessor import PreMigrationAssessor
from src.code_executor.upgrade_assistant import UpgradeAssistant

setup_logging("code_executor")
app = App(max_grpc_message_length=128 * 1024 * 1024)

semaphore = threading.Semaphore(1)


@app.method(name="execute_tests")
@timed()
def execute_tests(request: InvokeMethodRequest) -> InvokeMethodResponse:
    extract_trace_info(request)
    req_json = json.loads(request.text())
    source_project = CodeProject.model_validate(req_json["source_project"])
    test_project = CodeProject.model_validate(req_json["test_project"])
    target_language = req_json["target_language"]

    logging.info(f"got target_language: {target_language}")
    try:
        save_dir = generate_save_dir("code_executor")
        logging.info(f"source_language: {source_project.source_language}")

        if source_project.source_language == "dotnetframework":
            config = {
                "source_language": source_project.source_language,
                "testing_framework": "nunit",
            }
        elif source_project.source_language == "dotnet8":
            config = {
                "source_language": source_project.source_language,
                "testing_framework": "nunit",
            }
        elif (
            source_project.source_language == "java8"
            or source_project.source_language == "java21"
        ):
            config = {
                "source_language": source_project.source_language,
                "testing_framework": "junit",
            }
        elif source_project.source_language == "vba" and target_language == "dotnet8":
            config = {
                "source_language": source_project.source_language,
                "testing_framework": "nunit",
            }
        else:
            msg = f"unknown combination {source_project.source_language=} + {target_language=}"
            logging.error(msg)
            return InvokeMethodResponse(
                json.dumps(
                    {
                        "success": "false",
                        "error": msg,
                        "total_tests": -1,
                        "passed_tests": -1,
                        "failed_tests": 100,
                        "test_output": "",
                        "runtime": 1,
                    }
                )
            )

        ce = CodeExecutorFactory.create(config, source_project, test_project, save_dir)
        result: ExecutionResult = ce.execute()
    except Exception as e:
        if os.path.exists(save_dir) and len(os.listdir(save_dir)) != 0:
            # add error message as file
            with open(os.path.join(save_dir, "code_executor-error.txt"), "w") as f:
                f.write(str(e))

        # return success false and the error message
        logging.error(f"success: false; Error: {str(e)}")
        return InvokeMethodResponse(
            json.dumps(
                {
                    "success": "false",
                    "error": str(e),
                    "total_tests": -1,
                    "passed_tests": -1,
                    "failed_tests": 100,
                    "test_output": "",
                    "runtime": 1,
                }
            )
        )
    finally:
        # cleanup the generated files
        shutil.rmtree(save_dir, ignore_errors=True)

    if result.failed_tests == 0:
        logging.info("success: true")
        return InvokeMethodResponse(
            json.dumps(
                {
                    "success": "true",
                    "error": "",
                    "total_tests": result.total_tests,
                    "passed_tests": result.passed_tests,
                    "failed_tests": result.failed_tests,
                    "test_output": result.test_output,
                    "runtime": result.runtime,
                }
            )
        )
    else:
        logging.info("success: false")
        return InvokeMethodResponse(
            json.dumps(
                {
                    "success": "false",
                    "error": "",
                    "total_tests": result.total_tests,
                    "passed_tests": result.passed_tests,
                    "failed_tests": result.failed_tests,
                    "test_output": result.test_output,
                    "runtime": result.runtime,
                }
            )
        )


@app.method(name="call_upgrade_assistant")
@timed()
def call_upgrade_assistant(request: InvokeMethodRequest) -> InvokeMethodResponse:
    with semaphore:
        extract_trace_info(request)
        req_json = json.loads(request.text())
        source_project = CodeProject.model_validate(req_json["source_project"])
        target_language = req_json["target_language"]
        logging.info(f"got target_language: {target_language}")

        try:
            save_dir = generate_save_dir("upgrade_assistant")
            ua = UpgradeAssistant(source_project, save_dir)
            upgraded_project = ua.upgrade()
            return InvokeMethodResponse(
                json.dumps({"upgraded_project": upgraded_project.model_dump()})
            )
        except Exception as e:
            return InvokeMethodResponse(json.dumps({"error": str(e)}))
        finally:
            # cleanup the generated files
            shutil.rmtree(save_dir, ignore_errors=True)


@app.method(name="call_assess")
@timed()
def call_assess(request: InvokeMethodRequest) -> InvokeMethodResponse:
    extract_trace_info(request)
    req_json = json.loads(request.text())
    source_project = CodeProject.model_validate(req_json["source_project"])
    target_language = req_json["target_language"]
    logging.info(f"got target_language: {target_language}")

    if target_language != "dotnet8":
        msg = f"Unsupported target language: {target_language}"
        logging.error(msg)
        return InvokeMethodResponse(json.dumps({"error": msg}))

    try:
        save_dir = generate_save_dir("assessor")
        pre_migration_assessor = PreMigrationAssessor(source_project, save_dir)
        assessment_result = pre_migration_assessor.assess()
        return InvokeMethodResponse(
            json.dumps({"assessment_result": assessment_result.model_dump()})
        )
    except Exception as e:
        return InvokeMethodResponse(json.dumps({"error": str(e)}))
    finally:
        # cleanup the generated files
        shutil.rmtree(save_dir, ignore_errors=True)


if __name__ == "__main__":
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    backup_base_dir = config["backup_base_dir"]
    app.run(5001)
