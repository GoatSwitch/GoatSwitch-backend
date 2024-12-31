from abc import ABC, abstractmethod
from gs_common.CodeProject import CodeProject


class TestFormatter(ABC):
    @staticmethod
    @abstractmethod
    def format(project: CodeProject) -> CodeProject:
        pass
