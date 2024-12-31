from src.code_executor.test_formatter import TestFormatter
from gs_common.CodeProject import CodeProject


class JUnitTestFormatter(TestFormatter):
    @staticmethod
    def format(project: CodeProject) -> CodeProject:
        return project
