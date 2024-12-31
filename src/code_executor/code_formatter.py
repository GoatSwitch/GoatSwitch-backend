from abc import ABC, abstractmethod
from gs_common.CodeProject import CodeProject


class CodeFormatter(ABC):
    @staticmethod
    @abstractmethod
    def format(project: CodeProject) -> CodeProject:
        pass
