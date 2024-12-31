from abc import ABC, abstractmethod
from gs_common.CodeProject import CodeProject


class TestingFrameworkProgram(ABC):
    @abstractmethod
    def __init__(
        self,
        test_project: CodeProject,
        source_project: CodeProject,
        exec_dir: str,
    ):
        pass

    @abstractmethod
    def compile(self):
        pass

    @abstractmethod
    def run(self) -> float:
        pass

    @abstractmethod
    def check_results(self) -> tuple[int, str]:
        pass
