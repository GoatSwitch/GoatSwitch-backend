from gs_common.CodeProject import CodeProject
from langchain.prompts.chat import SystemMessagePromptTemplate

from src.goat_service.tl_generator.prompts.tl_prompter import (
    TLPrompter,
)
from src.goat_service.utils.operation_applier import (
    OP_USAGE,
    OperationApplier,
)

system_message = SystemMessagePromptTemplate.from_template(
    """\
You are a senior .NET 8 programmer. You will receive user requirements to improve a .NET 8 project.

{OP_USAGE}

"""
)

system_message = system_message.format(
    OP_USAGE=OP_USAGE,
)


class DotNet8ImproveTLPrompter(TLPrompter):
    system_message = system_message
    examples = []
    output_parser = None

    def convert_to_code_project(self, generation: str) -> tuple[CodeProject, bool]:
        da = OperationApplier(self.source_project, generation)
        return da.apply()
