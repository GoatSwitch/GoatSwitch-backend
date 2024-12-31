from gs_common.CodeProject import CodeProject

from src.goat_service.tl_generator.prompts.tl_prompter import TLPrompter
from src.goat_service.utils.operation_applier import OperationApplier


class UTPrompter(TLPrompter):
    # change this method to apply changes on the test project
    def convert_to_code_project(self, generation: str) -> tuple[CodeProject, bool]:
        da = OperationApplier(self.test_project, generation)
        new_project, success = da.apply()
        return new_project, success
