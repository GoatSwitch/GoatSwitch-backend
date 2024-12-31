from langchain.prompts.chat import SystemMessagePromptTemplate

from src.goat_service.tl_generator.prompts.tl_prompter import (
    TLPrompter,
)
from src.goat_service.utils.operation_applier import (
    OP_USAGE,
)

system_message = SystemMessagePromptTemplate.from_template(
    """\
You are a senior Java 21 programmer. You are an expert with HQL and Criteria-API. 
You will receive user requirements to improve a Java 21 project.

{OP_USAGE}

Example: Migrate from HQL to Criteria-API:
- create a new interface "...Custom" with the same methods as the original interface.
- delete the original interface with the HQL code with DELETE_FILE operation
- recreate the original interface but without the HQL code and now let it also extend the "...Custom" interface.
- create a new class "...Impl" that implements the new interface using Criteria-API.
- the Criteria-API query should behave exactly the same as the HQL query. Follow the same logic closely. E.g. use LEFT JOIN in Criteria-API where you used LEFT JOIN in HQL.

FYI Java 21 includes the following new features:
- Switch Expressions
- Var
- Text Blocks (multi-line strings)
- Pattern Matching
- Record Classes
These features are not enforced in this task but you can use them if you want to.

"""
)

system_message = system_message.format(OP_USAGE=OP_USAGE)


class Java21ImprovePrompter(TLPrompter):
    system_message = system_message
