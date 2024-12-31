import logging
import os
import subprocess
import time

from gs_common.CodeProject import CodeProject, ExecutionResult

from src.code_executor.code_formatter import CodeFormatter
from src.code_executor.test_formatter import TestFormatter
from src.code_executor.testing_framework_program import (
    TestingFrameworkProgram,
)
from src.code_executor.wrapper import Wrapper


class CodeExecutor:
    def __init__(
        self,
        source_code_formatter: CodeFormatter,
        test_code_formatter: TestFormatter,
        source_code_wrapper: Wrapper,
        testing_framework_program: TestingFrameworkProgram,
        source_project: CodeProject,
        test_project: CodeProject,
        exec_dir: str = None,
    ):
        self.exec_dir = exec_dir
        logging.info(f"Creating exec dir: {self.exec_dir}")
        os.makedirs(self.exec_dir, exist_ok=True)

        self.source_project = source_code_formatter.format(source_project)
        self.test_project = test_code_formatter.format(test_project)
        self.testing_framework_program = testing_framework_program

        if source_code_wrapper:
            self.source_project = source_code_wrapper.wrap(self.source_project)

    def execute(self) -> ExecutionResult:
        test_program: TestingFrameworkProgram = self.testing_framework_program(
            self.source_project,
            self.test_project,
            self.exec_dir,
        )
        try:
            start_time = time.time()
            test_program.compile()
            logging.info(
                f"Time to compile: {round(time.time() - start_time, 2)} seconds"
            )

            start_time = time.time()
            test_program.run()
            logging.info(f"Time to run: {round(time.time() - start_time, 2)} seconds")

            test_program.check_results()

        except subprocess.TimeoutExpired as e:
            raise Exception(
                f"TimeoutExpired.\n\nstdout: {e.stdout}\n\nstderr: {e.stderr}"
            )

        return ExecutionResult(
            total_tests=test_program.total_tests,
            passed_tests=test_program.passed_tests,
            failed_tests=test_program.failed_tests,
            test_output=test_program.test_output,
        )
