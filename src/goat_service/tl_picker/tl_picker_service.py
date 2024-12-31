import asyncio
import json
import logging
import os

from dapr.aio.clients import DaprClient
from dapr.ext.grpc import InvokeMethodRequest
from google.protobuf.json_format import MessageToDict
from gs_common.CodeProject import CodeFile, CodeProject, ExecutionResult
from gs_common.proto.common_pb2 import CodeProject as ProtoCodeProject
from gs_common.proto.tl_picker_pb2 import (
    ReturnCode,
    TLPickerRequest,
    TLPickerResponse,
)
from gs_common.tracing import current_company_id, extract_trace_info, inject_trace_info

from src.goat_service.tl_picker.most_changes_tl_picker import MostChangesTLPicker
from src.goat_service.tl_picker.tl_picker import TLPicker
from src.goat_service.utils.language_service_map import LANGUAGE_SERVICE_MAP
from src.goat_service.utils.user_metric_utils import log_user_metrics


class TLPickerService:
    def __init__(self):
        pass

    def pick_translation(self, request: InvokeMethodRequest) -> TLPickerResponse:
        logging.info("Happy easter from tl picker")
        extract_trace_info(request)
        req_proto = TLPickerRequest()
        request.unpack(req_proto)

        source_project = CodeProject.model_validate(
            MessageToDict(req_proto.source_project)
        )
        test_project = CodeProject.model_validate(MessageToDict(req_proto.test_project))
        tl_projects: list[CodeProject] = []
        for p in req_proto.translations:
            try:
                tl_projects.append(CodeProject.model_validate(MessageToDict(p)))
            except Exception as e:
                logging.error(f"Failed to parse project: {e}")
        logging.info(
            f"Got {len(tl_projects)} tl_projects for {source_project.display_name}"
        )

        target_language = req_proto.target_language
        log_user_metrics([source_project], target_language, stage="tlinput")
        log_user_metrics(tl_projects, target_language, stage="tleval")

        if target_language == "dotnetframework" or target_language == "dotnet8":
            tl_picker = TLPicker(source_project)
        elif target_language == "java8" or target_language == "java21":
            tl_picker = MostChangesTLPicker(source_project)
        else:
            logging.error(f"Unsupported target language: {target_language}")
            return TLPickerResponse(
                solution=ProtoCodeProject(source_language="", files=[]),
                test_output="",
                error=f"Unsupported target language: {target_language}",
                return_code=ReturnCode.ERROR,
            )

        results: list[ExecutionResult] = asyncio.run(
            self._execute_tests(tl_projects, test_project, target_language)
        )

        # loop through results and log exceptions
        for result in results:
            if isinstance(result, Exception):
                logging.error(
                    f"Failed to execute tl_project: {result.project.display_name}. Got exception: {result}"
                )
                continue

        # remove exceptions from results
        results = [r for r in results if not isinstance(r, Exception)]

        # case: no tl_project could be executed
        if len(results) == 0:
            msg = "No tl_project could be executed! Returning first one."
            logging.error(msg)
            try:
                msg_error = results[0].error
            except Exception:
                msg_error = "No test compiled, but no error received!"
            return TLPickerResponse(
                solution=ProtoCodeProject(**tl_projects[0].model_dump()),
                error=msg_error,
                return_code=ReturnCode.FAILED_TEST_COMPILE,
            )

        # find best test_project
        best_result = tl_picker.pick_best(results)
        if best_result is None:
            logging.error("Best tl_project is None! Returning first.")
            best_result = results[0]

        # case: best tl_project has compilation error
        if best_result.error != "":
            logging.error("Best solution has compilation error")
            return TLPickerResponse(
                solution=ProtoCodeProject(**best_result.project.model_dump()),
                error=best_result.error,
                test_output=best_result.test_output,
                return_code=ReturnCode.FAILED_TEST_COMPILE,
            )

        log_user_metrics([best_result.project], target_language, stage="tloutput")

        # case: best tl_project has failed tests
        if not best_result.success:
            msg = "Some tests failed!"
            logging.error(msg)
            return TLPickerResponse(
                solution=ProtoCodeProject(**best_result.project.model_dump()),
                error=msg,
                test_output=best_result.test_output,
                return_code=ReturnCode.FAILED_TEST_EXECUTION,
            )

        # case: solution found
        n_successful_tl_projects = len([r for r in results if r.success])
        logging.info(f"Found {n_successful_tl_projects=}")
        # add metrics for benchmarking
        if current_company_id.get() == "9999":
            best_result.project.files.append(
                CodeFile(
                    file_name=".gs_metrics",
                    source_code=f"GSMETRIC:{n_successful_tl_projects=}",
                )
            )
        return TLPickerResponse(
            solution=ProtoCodeProject(**best_result.project.model_dump()),
            test_output=best_result.test_output,
            return_code=ReturnCode.SUCCESS,
        )

    async def _execute_tests(
        self, tl_projects, test_project, target_language
    ) -> list[ExecutionResult]:
        tasks = []
        for tl_project in tl_projects:
            data = {
                "source_project": tl_project.model_dump(),
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
        if len(responses) != len(tl_projects):
            logging.error(
                f"len(responses): {len(responses)} != len(tl_projects): {len(tl_projects)}"
            )
            # just continue; cannot be fixed

        results = []
        for tl_project, response in zip(tl_projects, responses):
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
                project=tl_project,
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
