from langchain.prompts.chat import SystemMessagePromptTemplate

from src.goat_service.tl_generator.prompts.tl_prompter import TLPrompter
from src.goat_service.utils.operation_applier import OP_USAGE

system_message = SystemMessagePromptTemplate.from_template(
    """\
You are a senior software engineer.
You will receive user requirements to improve a code project.

{OP_USAGE}
"""
)

system_message = system_message.format(OP_USAGE=OP_USAGE)


class UniversalTLPrompter(TLPrompter):
    system_message = system_message
