from abc import ABC, abstractmethod
from gs_common.CodeProject import CodeProject


class Wrapper(ABC):
    @staticmethod
    @abstractmethod
    def wrap(project: CodeProject) -> CodeProject:
        pass
