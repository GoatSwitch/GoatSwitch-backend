import asyncio
import json
import logging
import os

from dapr.aio.clients import DaprClient
from dapr.ext.grpc import InvokeMethodRequest
from google.protobuf.json_format import MessageToDict
from gs_common.CodeProject import CodeProject, ExecutionResult
from gs_common.proto.common_pb2 import CodeProject as ProtoCodeProject
from gs_common.proto.ut_picker_pb2 import ReturnCode, UTPickerRequest, UTPickerResponse
from gs_common.tracing import extract_trace_info, inject_trace_info

from src.goat_service.ut_picker.ut_picker import UTPicker
from src.goat_service.ut_picker.nunit_ut_picker import NUnitUTPicker
from src.goat_service.utils.language_service_map import LANGUAGE_SERVICE_MAP
from src.goat_service.utils.user_metric_utils import log_user_metrics


class UTPickerService:
    def __init__(self):
        pass

    def pick_unittests(
        self,
        request: InvokeMethodRequest,
    ) -> UTPickerResponse:
        extract_trace_info(request)
        req_proto = UTPickerRequest()
        request.unpack(req_proto)

        source_project = CodeProject.model_validate(
            MessageToDict(req_proto.source_project)
        )
        target_language = req_proto.target_language
        test_projects: list[CodeProject] = [
            CodeProject.model_validate(MessageToDict(p))
            for p in req_proto.test_projects
        ]
        log_user_metrics([source_project], target_language, stage="utinput")
        log_user_metrics(test_projects, target_language, stage="uteval")

        if target_language == "dotnetframework" or target_language == "dotnet8":
            ut_picker = NUnitUTPicker(source_project)
        elif target_language == "java8" or target_language == "java21":
            ut_picker = UTPicker(source_project)
        else:
            logging.error(f"Unsupported target language: {target_language}")
            return UTPickerResponse(
                error="Unsupported target language: {target_language}",
                return_code=ReturnCode.ERROR,
            )

        logging.info(
            f"Got {len(test_projects)} test_projects to execute for source_project: {source_project.display_name}"
        )
        results: list[ExecutionResult] = asyncio.run(
            self._execute_tests(source_project, test_projects, target_language)
        )

        # loop through results and log exceptions
        for result in results:
            if isinstance(result, Exception):
                logging.error(
                    f"Failed to execute test_project: {result.project.display_name}. Got exception: {result}"
                )
                continue

        # remove exceptions from results and test_projects
        results = [r for r in results if not isinstance(r, Exception)]

        # case: no test_project could be executed
        if len(results) == 0:
            msg = "No test_project could be executed! Returning first one."
            logging.error(msg)
            try:
                msg_error = results[0].error
            except Exception:
                msg_error = "No test compiled, but no error received!"
            return UTPickerResponse(
                solution=ProtoCodeProject(**test_projects[0].model_dump()),
                error=msg_error,
                return_code=ReturnCode.FAILED_TEST_COMPILE,
            )

        # find best test_project
        best_result = ut_picker.pick_best(results)
        if best_result is None:
            logging.error(
                "Best result of Unittestpicker is None! Returning first test_project."
            )
            best_result = results[0]

        log_user_metrics([best_result.project], target_language, stage="utoutput")

        # case: best test project has failed tests
        if not best_result.success:
            msg = "Some tests failed on source project!"
            logging.error(msg)
            # set error message to compilation error if available
            if best_result.error:
                msg = f" Error: {best_result.error}"
            return UTPickerResponse(
                solution=ProtoCodeProject(**best_result.project.model_dump()),
                error=msg,
                test_output=best_result.test_output,
                return_code=ReturnCode.FAILED_TEST_EXECUTION,
            )

        # case: solution found
        return UTPickerResponse(
            solution=ProtoCodeProject(**best_result.project.model_dump()),
            test_output=best_result.test_output,
            return_code=ReturnCode.SUCCESS,
        )

    async def _execute_tests(
        self, source_project, test_projects, target_language
    ) -> list[ExecutionResult]:
        tasks = []
        for test_project in test_projects:
            data = {
                "source_project": source_project.model_dump(),
                "test_project": test_project.model_dump(),
                "target_language": target_language,
            }

            async with DaprClient(headers_callback=inject_trace_info) as d:
                service_name = LANGUAGE_SERVICE_MAP.get(
                    target_language, "code-executor"
                )
                task = d.invoke_method(
                    service_name,
                    "execute_tests",
                    data=json.dumps(data),
                    timeout=60 * 5,
                )
                tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        if len(responses) != len(test_projects):
            logging.error(
                f"len(responses): {len(responses)} != len(test_projects): {len(test_projects)}"
            )
            # just continue; cannot be fixed

        results = []
        for test_project, response in zip(test_projects, responses):
            if isinstance(response, Exception):
                results.append(response)
                continue
            response = json.loads(response.data)
            # TODO: better solution
            max_error_length = 10_000
            if len(response["error"]) > max_error_length:
                logging.error(
                    f"Error message is too long: {len(response['error'])} characters. Truncating to {max_error_length} characters."
                )
                response["error"] = response["error"][:max_error_length]

            result = ExecutionResult(
                project=test_project,
                success=True if response["success"] == "true" else False,
                error=response["error"],
                total_tests=int(response["total_tests"]),
                passed_tests=int(response["passed_tests"]),
                failed_tests=int(response["failed_tests"]),
                test_output=response["test_output"],
                runtime=int(response["runtime"]),
            )
            results.append(result)
        return results
