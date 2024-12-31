import logging
import os
import subprocess
import xml.etree.ElementTree as ET

from gs_common.CodeProject import CodeProject

from src.code_executor.testing_framework_program import (
    TestingFrameworkProgram,
)


class NUnitProgram(TestingFrameworkProgram):
    def __init__(
        self,
        source_project: CodeProject,
        test_project: CodeProject,
        exec_dir: str,
    ):
        self.source_project = source_project
        self.exec_dir = exec_dir

        if self.source_project.source_language == "dotnetframework":
            self.is_dotnetframework = True
        elif self.source_project.source_language == "dotnet8":
            self.is_dotnetframework = False
        else:
            raise ValueError(
                f"Language not supported: {self.source_project.source_language}"
            )

        self.source_csproj_filename = self._get_csproj_filename(source_project)
        self.test_csproj_filename = self._get_csproj_filename(test_project)

        # basename of the path without .csproj
        self.source_project_name = os.path.basename(
            self.source_csproj_filename
        ).replace(".csproj", "")
        self.test_project_name = os.path.basename(self.test_csproj_filename).replace(
            ".csproj", ""
        )

        self.source_project_dir = os.path.join(self.exec_dir, self.source_project_name)
        # NOTE: test project must be -GSTests (to work with SetInternalsVisibleToTestProject)
        self.test_project_dir = os.path.join(
            self.exec_dir, self.source_project_name + "-GSTests"
        )

        self.dotnet_compile_dir = os.path.join(
            self.source_project_dir, os.path.dirname(self.source_csproj_filename)
        )

        self._handle_dotnet_versions()
        self._set_test_project_placeholders(test_project)

        test_project.save_to_dir(self.test_project_dir)
        self.source_project.save_to_dir(self.source_project_dir)

    def _get_csproj_filename(self, source_project: CodeProject) -> str:
        # search in files, not reference files
        for file in source_project.files:
            if file.file_name.endswith(".csproj"):
                return file.file_name
        raise Exception(f"No csproj file found in {source_project.display_name}")

    def _handle_dotnet_versions(self):
        """
        Extract the target framework from the source project csproj file
        If the csproj file is in the old style, set the dotnet version to net48
        If the csproj file is in the new style, set the dotnet version to the highest version
        If the dotnet version contains -windows, remove the specific windows version to compile on current OS
        """
        csproj_file = self.source_project.get_file(self.source_csproj_filename)
        self.old_csproj_style = self._old_csproj_style(csproj_file.source_code)
        if self.old_csproj_style:
            # NOTE: it is called "v4.8" in the old csproj files but lets use new name here for clarity
            self.dotnet_version = "net48"
            self.is_windows_only = True
        else:
            # extract target framework from csproj
            if "<TargetFramework>" in csproj_file.source_code:
                version_string = csproj_file.source_code.split("<TargetFramework>")[
                    1
                ].split("</TargetFramework>")[0]
                self.dotnet_version = version_string
            elif "<TargetFrameworks>" in csproj_file.source_code:
                version_string = csproj_file.source_code.split("<TargetFrameworks>")[
                    1
                ].split("</TargetFrameworks>")[0]
                versions = version_string.split(";")
                # sort versions to get the highest one; but set netcore and netstandard to the lowest
                versions.sort(
                    key=lambda x: 0
                    if "netcore" in x
                    else 1
                    if "netstandard" in x
                    else 2
                )
                self.dotnet_version = versions[-1]
            else:
                raise Exception(
                    f"Could not find <TargetFramework(s)> in csproj: {csproj_file.source_code}"
                )

            # NOTE: specific windows version will lead to error if not running on same OS
            # -> remove specific windows version to compile on current OS
            # -> who needs a specific windows verion anyway, should be fine...
            if "-windows" in self.dotnet_version:
                # e.g. from net5.0-windows10.0.19041.0 to net5.0-windows
                self.dotnet_version = (
                    self.dotnet_version.split("-windows")[0] + "-windows"
                )

                # now change source project csproj target framework to the new version
                csproj_file.source_code = csproj_file.source_code.replace(
                    version_string, self.dotnet_version
                )
                self.source_project.add_file(
                    file_name=csproj_file.file_name,
                    source_code=csproj_file.source_code,
                )

            self.is_windows_only = "-windows" in self.dotnet_version

        logging.info(f"old csproj style: {self.old_csproj_style}")
        logging.info(f"dotnet version: {self.dotnet_version}")
        logging.info(f"is windows only: {self.is_windows_only}")

    def _old_csproj_style(self, csproj_code: str) -> bool:
        new_csproj_style = (
            csproj_code.strip()
            .lower()
            # can be normal Microsoft.NET.Sdk or specials like Microsoft.NET.Sdk.Razor
            .startswith('<Project Sdk="Microsoft.NET.Sdk'.lower())
        )
        return not new_csproj_style

    def _set_test_project_placeholders(self, test_project: CodeProject):
        # find the test project file
        for file in test_project.files:
            if file.file_name.endswith(".csproj"):
                lines = file.source_code.split("\n")
                for line_idx, line in enumerate(lines):
                    if "<TargetFramework>" in line:
                        if self.is_dotnetframework:
                            lines[line_idx] = "<TargetFramework>net48</TargetFramework>"
                        else:
                            # set same target framework as source project
                            lines[line_idx] = (
                                f"<TargetFramework>{self.dotnet_version}</TargetFramework>"
                            )
                    if "<ProjectReference Include=" in line:
                        lines[line_idx] = (
                            f'<ProjectReference Include="../{self.source_project_name}/{self.source_csproj_filename}" />'
                        )

                # replace the source code with the modified lines
                file.source_code = "\n".join(lines)
                break
        else:
            raise Exception("No csproj file found in test project")

    def compile(self):
        # restore packages
        if self.old_csproj_style:
            packages_config_path = self._get_packages_config_path()
            if packages_config_path:
                # TODO: dont do msbuild restore after nuget restore
                #  + remove nuget.targets from csproj
                # restore packages via nuget before building
                logging.info("Restoring packages with nuget")
                command = [
                    "nuget",
                    "restore",
                    packages_config_path,
                    "-PackagesDirectory",
                    "packages",
                ]
                self._run_command(command, self.dotnet_compile_dir)
            command = ["msbuild", "/t:restore", "/t:build"]
        else:
            command = ["dotnet", "build"]
        self._run_command(command, self.test_project_dir)

    def _get_packages_config_path(self):
        # NOTE: our projects have only one csproj for now
        # NOTE: assumption: packages.config is in the same directory as csproj
        # NOTE: this is mostly true for the github projects
        # return relative path to packages.config file
        for file in os.listdir(self.dotnet_compile_dir):
            if file.endswith("packages.config"):
                return file
        return None

    def _run_command(self, command, cwd):
        self.process_result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd,
        )
        self._check_subprocess_result(command, self.process_result)

    def run(self):
        # use nunit3-console to execute the tests
        if self.old_csproj_style:
            logging.info("Running tests with nunit3-console")
            nunit_runner = os.path.join(
                os.path.expanduser("~"),
                ".nuget/packages/nunit.consolerunner/3.16.3/tools/nunit3-console.exe",
            )
            command = [
                nunit_runner,
                f"bin/Debug/net48/{self.test_project_name}.dll",
                "--result=test_results.xml",
            ]
            if os.name != "nt":  # Windows
                command = ["mono"] + command
        else:
            command = [
                "dotnet",
                "test",
                "--logger",
                "nunit;LogFileName=test_results.xml",
            ]
        self._run_command(command, self.test_project_dir)
        return self._get_runtime()

    def check_results(self):
        # parse the test_results.xml file
        # we only need this line:
        # <test-run id="0" runstate="Runnable" testcasecount="3" result="Failed" total="3" passed="2" failed="1" warnings="0" ...
        # parse the result attribute and number of failed tests
        if self.old_csproj_style:
            result_file = os.path.join(self.test_project_dir, "test_results.xml")
        else:
            result_file = os.path.join(
                self.test_project_dir, "TestResults", "test_results.xml"
            )
        tree = ET.parse(result_file)
        root = tree.getroot()
        # return the xml as string
        self.test_output = ET.tostring(root, encoding="unicode")
        result = root.attrib["result"]
        self.total_tests = int(root.attrib["total"])
        self.passed_tests = int(root.attrib["passed"])
        self.failed_tests = int(root.attrib["failed"])
        if self.total_tests == 0:
            logging.error(
                f"No tests found: {self.source_project.display_name}, {self.total_tests=}, {self.passed_tests=}, {self.failed_tests=}"
            )
            self.failed_tests = 100
        if self.failed_tests == 0 and result == "Failed" and self.total_tests > 0:
            # weird case where no tests failed but result is failed
            logging.error(
                f"No tests failed but result is failed: {self.source_project.display_name}, {self.total_tests=}, {self.passed_tests=}, {self.failed_tests=}"
            )
            self.failed_tests = 100

    def _check_subprocess_result(
        self, command, process_result: subprocess.CompletedProcess
    ):
        logging.info(
            "stdout: ------------------------------------\n" + process_result.stdout
        )
        logging.info(
            "stderr: ------------------------------------\n" + process_result.stderr
        )

        if "Build FAILED." in process_result.stdout or process_result.stderr != "":
            raise Exception(
                f"{command[0]} error:\n\nSTDOUT: {process_result.stdout}\n\nSTDERR: {process_result.stderr}"
            )

    def _get_runtime(self) -> float:
        if self.old_csproj_style:
            result_file = os.path.join(self.test_project_dir, "test_results.xml")
        else:
            result_file = os.path.join(
                self.test_project_dir, "TestResults", "test_results.xml"
            )
        tree = ET.parse(result_file)
        root = tree.getroot()
        self.runtime = float(root.attrib["duration"]) * 1000
