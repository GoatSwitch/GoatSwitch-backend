from dataclasses import dataclass

from gs_common.CodeProject import CodeProject
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts.chat import SystemMessagePromptTemplate
from pydantic import BaseModel

from src.goat_service.tl_generator.prompts.tl_prompter import (
    TLPrompter,
)

BUILT_IN_OPERATIONS_WITH_USAGE = {
    "UPGRADE_DOTNET_PROJECT": """
    Use to upgrade any .NET project to the latest .NET version.
    """,
    "RENAME_VARIABLE": """
    Use to rename all occurrences of a string in a file.
    Usage:
    Operation name: RENAME_VARIABLE
    Description: Use <rename_variable old_name="old_name" new_name="new_name" file_path="file_path" />
    """,
    "RENAME_VARIABLE_GLOBAL": """
    Use to rename all occurrences of a string in all files.
    Usage:
    Operation name: RENAME_VARIABLE_GLOBAL
    Description: Use <rename_variable_global old_name="old_name" new_name="new_name" />
    """,
    "GENERATE_TESTS": """
    Use to generate tests for a method or class.
    If you want to generate tests for multiple methods or classes, make multiple steps with this operation.
    One step should only generate about 3 tests.
    The tests will be executed automatically after generation.
    """,
}


@dataclass
class Operation:
    operation_name: str
    description: str


class AIPlan(BaseModel):
    operations: list[Operation]

    def __str__(self):
        if not self.operations:
            raise ValueError("No operations in plan")
        plan = "# AI Plan\n"
        for i, operation in enumerate(self.operations):
            plan += f"## Step {i+1}: {operation.operation_name}\n"
            plan += f"{operation.description}\n"
        return plan

    @classmethod
    def from_string(cls, plan: str):
        operations = []
        for line in plan.split("\n"):
            if line.lower().startswith("# Current Task:".lower()):
                # do not parse the rest of the plan
                break
            if line.startswith("## Step"):
                operation = Operation(
                    description="", operation_name=line.split(":")[1].strip()
                )
                operations.append(operation)
            elif line and operations:
                operations[-1].description += line + "\n"
        if not operations:
            raise ValueError(f"Cannot parse plan ({plan})")
        return cls(operations=operations)


output_parser = PydanticOutputParser(pydantic_object=AIPlan)

system_message = SystemMessagePromptTemplate.from_template(
    """\
You are a senior software architect.
You will receive user requirements to improve a code project.

Your task is to generate a high level plan to improve the code project according to the user instructions.
Your plan must consist of a list of high level operations that need to be performed to improve the project.
When possible, use built-in operations to perform the tasks.
If no built-in operation is available, create a custom operation.
The custom operations can only be about editing the code manually.
You cannot perform other actions like running tests or deploying the project.

You must add a description to each operation to explain what needs to be done in more detail.

Your output must be a valid json like this:
{json_output_schema}
"""
)

system_message = system_message.format(
    json_output_schema=output_parser.get_format_instructions(),
)

ADDITIONAL_INFO = """
List of built-in operations and their usage:
{built_in_ops}
""".format(
    built_in_ops="\n".join(
        f"- {op_name}: {op_usage}"
        for op_name, op_usage in BUILT_IN_OPERATIONS_WITH_USAGE.items()
    )
)


class UniversalPlanPrompter(TLPrompter):
    system_message = system_message
    examples = []
    output_parser = output_parser

    def get_additional_info(self) -> str:
        return ADDITIONAL_INFO

    def convert_to_code_project(self, generation: str) -> tuple[CodeProject, bool]:
        operation_plan: AIPlan = self.output_parser.parse(generation)
        return operation_plan, True
