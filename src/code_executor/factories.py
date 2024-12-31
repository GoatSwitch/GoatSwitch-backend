from src.code_executor.code_executor import CodeExecutor
from src.code_executor.code_formatter import CodeFormatter
from src.code_executor.dotnet8_code_formatter import Dotnet8CodeFormatter
from src.code_executor.dotnetframework_code_formatter import (
    DotnetFrameworkCodeFormatter,
)
from src.code_executor.java8_code_formatter import Java8CodeFormatter
from src.code_executor.java21_code_formatter import Java21CodeFormatter
from src.code_executor.junit_program import JUnitProgram
from src.code_executor.junit_test_formatter import JUnitTestFormatter
from src.code_executor.nunit_program import NUnitProgram
from src.code_executor.nunit_test_formatter import NUnitTestFormatter
from src.code_executor.test_formatter import TestFormatter
from src.code_executor.testing_framework_program import (
    TestingFrameworkProgram,
)
from src.code_executor.wrapper import Wrapper


class CodeExecutorFactory:
    @staticmethod
    def create(
        config: dict,
        source_project: str,
        test_project: str,
        save_dir: str,
    ) -> CodeExecutor:
        # check if config is valid
        CodeExecutorFactory.check_config(config)

        code_formatter = CodeFormatterFactory.create(config["source_language"])
        test_formatter = TestFormatterFactory.create(config["testing_framework"])
        source_code_wrapper = WrapperFactory.create(config["source_language"])
        testing_framework_program = TestingFrameworkProgramFactory.create(
            config["testing_framework"]
        )
        return CodeExecutor(
            code_formatter,
            test_formatter,
            source_code_wrapper,
            testing_framework_program,
            source_project,
            test_project,
            save_dir,
        )

    @staticmethod
    def check_config(config: dict):
        # available configs
        dotnetframework_config = {
            "source_language": "dotnetframework",
            "testing_framework": "nunit",
        }
        dotnet8_config = {
            "source_language": "dotnet8",
            "testing_framework": "nunit",
        }
        java8_config = {
            "source_language": "java8",
            "testing_framework": "junit",
        }
        java21_config = {
            "source_language": "java21",
            "testing_framework": "junit",
        }

        if config in [
            dotnetframework_config,
            dotnet8_config,
            java8_config,
            java21_config,
        ]:
            return
        else:
            raise ValueError("Config not supported")


class CodeFormatterFactory:
    @staticmethod
    def create(language: str) -> CodeFormatter:
        if language == "dotnetframework":
            return DotnetFrameworkCodeFormatter
        elif language == "dotnet8":
            return Dotnet8CodeFormatter
        elif language == "java8":
            return Java8CodeFormatter
        elif language == "java21":
            return Java21CodeFormatter
        else:
            raise ValueError("Language not supported")


class TestFormatterFactory:
    @staticmethod
    def create(testing_framework: str) -> TestFormatter:
        if testing_framework == "nunit":
            return NUnitTestFormatter
        elif "junit" in testing_framework:
            return JUnitTestFormatter
        else:
            raise ValueError("Testing framework not supported")


class WrapperFactory:
    @staticmethod
    def create(language: str) -> Wrapper:
        if language == "dotnet8":
            return None
        elif language == "dotnetframework":
            return None
        elif language == "java8":
            return None
        elif language == "java21":
            return None
        else:
            raise ValueError("Target compiler not supported")


class TestingFrameworkProgramFactory:
    @staticmethod
    def create(testing_framework: str) -> TestingFrameworkProgram:
        if testing_framework == "nunit":
            return NUnitProgram
        elif testing_framework == "junit":
            return JUnitProgram
        else:
            raise ValueError("Testing framework not supported")
