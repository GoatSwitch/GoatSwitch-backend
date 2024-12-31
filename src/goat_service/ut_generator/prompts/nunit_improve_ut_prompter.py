from langchain.prompts.chat import SystemMessagePromptTemplate

from src.goat_service.ut_generator.prompts.ut_prompter import UTPrompter
from src.goat_service.utils.operation_applier import OP_USAGE

system_message = SystemMessagePromptTemplate.from_template(
    """\
You are a senior .NET 8 programmer. You will receive user requirements to improve a .NET 8 project.
Specifically you will receive a source project, a test project and instruction on how to improve the test project.

{OP_USAGE}

The operations will be applied to the *test* code files in the order they are generated.

"""
)

system_message = system_message.format(
    OP_USAGE=OP_USAGE,
)


class NUnitImproveUTPrompter(UTPrompter):
    system_message = system_message
