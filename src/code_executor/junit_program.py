import logging
import os
import re
import subprocess

from gs_common.CodeProject import CodeProject
from junitparser import JUnitXml

from src.code_executor.testing_framework_program import (
    TestingFrameworkProgram,
)

GRADLE_CONFIG = {
    "command": ["gradle", "test", "--build-cache", "--no-daemon"],
    "build_file": "build.gradle",
    "test_results_dir": "build/test-results/test",
    "success_message": "BUILD SUCCESSFUL",
    "failing_tests_message": "There were failing tests",
}

MAVEN_CONFIG = {
    "command": ["mvn", "test"],
    "build_file": "pom.xml",
    "test_results_dir": "target/surefire-reports",
    "success_message": "BUILD SUCCESS",
    "failing_tests_message": "There are test failures.",
}


class JUnitProgram(TestingFrameworkProgram):
    def __init__(
        self,
        source_project: CodeProject,
        test_project: CodeProject,
        exec_dir: str,
    ):
        self.source_project = source_project
        self.exec_dir = exec_dir

        if self.source_project.source_language == "java8":
            self.is_java8 = True
        elif self.source_project.source_language == "java21":
            self.is_java8 = False
        else:
            raise ValueError(
                f"Language not supported: {self.source_project.source_language}"
            )

        # find out compiler
        pom_file = source_project.get_file("pom.xml")
        if not pom_file:
            # try gradle
            gradle_file = source_project.get_file("build.gradle")
            if not gradle_file:
                raise ValueError(
                    "No build file found (pom.xml or build.gradle); cannot determine compiler"
                )
            self.config = GRADLE_CONFIG
        else:
            self.config = MAVEN_CONFIG

        self.source_project_dir = os.path.join(
            self.exec_dir, self.source_project.display_name
        )

        # save exec project to dir
        self.source_project.save_to_dir(self.source_project_dir)

        self.compile_only = True
        if test_project is not None:
            self.compile_only = False
            # we always use the build file from source project
            # remove build file from test project
            test_project.remove_file(self.config["build_file"])
            # save test project to same dir as source project
            test_project.save_to_dir(self.source_project_dir)
            if self.config["build_file"] == "pom.xml":
                # using other test dir than default is hard with pom...
                # rename GSTests to test
                os.rename(
                    os.path.join(self.source_project_dir, "src", "GSTests"),
                    os.path.join(self.source_project_dir, "src", "test"),
                )

        # test output dir
        self.test_results_dir = os.path.join(
            self.source_project_dir, self.config["test_results_dir"]
        )

    def compile(self):
        pass

    def _run_command(self, command, cwd, timeout=220):
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            raise
        self.process_result = subprocess.CompletedProcess(
            command, process.returncode, stdout, stderr
        )
        self._check_subprocess_result(command, self.process_result)

    def run(self):
        self._run_command(self.config["command"], self.source_project_dir)
        return self._get_runtime()

    def check_results(self):
        if self.compile_only:
            self.test_output = 'tests="1" failures="0" errors="0" skipped="0"'
            self.total_tests = 1
            self.passed_tests = 1
            self.failed_tests = 0
            return

        self.test_output = self._read_and_merge_junit_xml_files()
        # we only need this line:
        # <testsuites tests="8" failures="0" errors="0" skipped="0" time="0.603"><
        # parse the result attribute and number of failed tests
        match = re.search(
            r'tests="(\d+)" failures="(\d+)" errors="(\d+)" skipped="(\d+)"',
            self.test_output,
        )
        self.total_tests = int(match.group(1))
        self.failed_tests = int(match.group(2))
        n_errors = int(match.group(3))
        n_skipped = int(match.group(4))
        self.failed_tests += n_errors + n_skipped
        self.passed_tests = self.total_tests - self.failed_tests
        logging.info(
            f"JUnit test results: total={self.total_tests}, passed={self.passed_tests}, failed={self.failed_tests}, errors={n_errors}, skipped={n_skipped}"
        )

        if self.total_tests == 0:
            # case: empty test suite (e.g. no tests compiled)
            self.failed_tests = 100
        if n_errors > 0:
            # case: compilation error
            self.failed_tests = 100
        # TODO: case: test suite has only empty methods
        # TODO: case: code does not compile but tests are executed

    def _check_subprocess_result(
        self, command, process_result: subprocess.CompletedProcess
    ):
        # remove ansi escape codes
        ansi_escape_pattern = re.compile(r"\x1b\[[0-9;]*m")
        process_result.stdout = ansi_escape_pattern.sub("", process_result.stdout)
        process_result.stderr = ansi_escape_pattern.sub("", process_result.stderr)

        logging.info(
            "stdout: ------------------------------------\n" + process_result.stdout
        )
        logging.info(
            "stderr: ------------------------------------\n" + process_result.stderr
        )

        if self.config["success_message"] in process_result.stdout:
            return

        if (
            self.config["failing_tests_message"] in process_result.stdout
            or self.config["failing_tests_message"] in process_result.stderr
        ):
            # do not raise exeption, check results later
            return

        raise Exception(
            f"{command[0]} error:\n\nSTDOUT: {process_result.stdout}\n\nSTDERR: {process_result.stderr}"
        )

    def _get_runtime(self) -> float:
        self.runtime = 1

    def _read_and_merge_junit_xml_files(self) -> str:
        # there are multiple xml files in the test_results_dir
        xml_files = [
            os.path.join(self.test_results_dir, file)
            for file in os.listdir(self.test_results_dir)
            if file.endswith(".xml")
        ]
        if not xml_files:
            raise FileNotFoundError(
                f"No test result file found in dir: {self.test_results_dir}; files: {os.listdir(self.test_results_dir)}"
            )

        # merge all xml files w junitparser
        xml_merged = JUnitXml()
        for file in xml_files:
            xml = JUnitXml.fromfile(file)
            xml_merged += xml

        # return as string
        return xml_merged.tostring().decode("utf-8")
