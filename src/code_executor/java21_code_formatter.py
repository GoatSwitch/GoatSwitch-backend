import xml.etree.ElementTree as ET

from src.code_executor.code_formatter import CodeFormatter
from gs_common.CodeProject import CodeProject


class Java21CodeFormatter(CodeFormatter):
    @staticmethod
    def format(project: CodeProject) -> CodeProject:
        return project
