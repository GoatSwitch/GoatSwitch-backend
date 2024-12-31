import logging
import os

from gs_common.CodeProject import CodeFile, CodeProject
from langchain.prompts.chat import SystemMessagePromptTemplate

from src.goat_service.ut_generator.prompts.ut_prompter import UTPrompter
from src.goat_service.utils.operation_applier import OP_USAGE, OperationApplier

system_message = SystemMessagePromptTemplate.from_template(
    """\
You are a senior software engineer specialized in unit testing.
You will receive user requirements to generate unit tests for a code project.

General guidelines:
- If working with .Net, use the NUnit framework.
- If working with Java, use JUnit.
- If not otherwise necessary, save the test files in the base directory of the test project. (The file path will be relative to the project folder, so you do not need to specify the project folder in the file path.)

{OP_USAGE}

The operations will be applied to the *test* code files in the order they are generated.
The source code cannot be modified.
"""
)

system_message = system_message.format(OP_USAGE=OP_USAGE)


class UniversalUTPrompter(UTPrompter):
    system_message = system_message

    def __init__(
        self,
        source_project: CodeProject,
        instruction: str = None,
        test_project: CodeProject = None,
    ):
        super().__init__(source_project, instruction, test_project)

        if self.test_project is not None and len(self.test_project.files) > 0:
            # when we start with a test project that has files; do not modify it
            return

        # create empty test project if not provided; to save generated files to later
        if self.test_project is None or len(self.test_project.files) == 0:
            self.test_project = CodeProject(
                display_name=f"{source_project.display_name}-GSTests",
                source_language=source_project.source_language,
                files=[],
            )

        # TODO: make for java
        if (
            source_project.source_language != "dotnetframework"
            and source_project.source_language != "dotnet8"
        ):
            return

        ### Add csproj if dotnet
        # Search source csproj file
        source_csprojs = [
            f for f in self.source_project.files if f.file_name.endswith(".csproj")
        ]
        # there may only be one csproj file
        if len(source_csprojs) != 1:
            logging.error(
                f"Expected one csproj file in source project, found {len(source_csprojs)}: {[f.file_name for f in source_csprojs]}"
            )
            return

        # get rid of the path
        csproj_file_name = os.path.basename(source_csprojs[0].file_name)
        # get rid of .csproj
        csproj_file_name = csproj_file_name.replace(".csproj", "")
        # Load csproj template
        path = os.path.join(
            "templates", "csharp", "UniversalTestProjectTemplate.csproj"
        )
        try:
            with open(path, "r") as f:
                csproj_template = f.read()
        except Exception as e:
            logging.error(f"Error loading file {path}: {e}")
            return

        # create new csproj CodeFile
        csproj = CodeFile(
            file_name=f"{csproj_file_name}-GSTests.csproj",
            source_code=csproj_template,
        )
        # replace <ProjectReference Include="RELATIVE_PATH_TO_LIBRARY_CSPROJ" />
        csproj.source_code = csproj.source_code.replace(
            "RELATIVE_PATH_TO_LIBRARY_CSPROJ",
            f"../{csproj_file_name}/{csproj_file_name}.csproj",
        )
        self.test_project.files.append(csproj)
