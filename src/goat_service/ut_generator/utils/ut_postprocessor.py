import os

from gs_common.CodeProject import CodeFile, CodeProject


class UnitTestPostProcessor:
    def __init__(self, source_project: CodeProject) -> None:
        self.source_project = source_project
        self.dotnet_hardcoded_csproj_file = None
        self.use_dotnet_csproj = False

    def load_dotnet_csproj(self) -> str:
        self.use_dotnet_csproj = True
        # Search source csproj file
        source_csprojs = [
            f for f in self.source_project.files if f.file_name.endswith(".csproj")
        ]
        # there may only be one csproj file
        if len(source_csprojs) != 1:
            raise ValueError(
                f"Expected one csproj file in source project, found {len(source_csprojs)}: {[f.file_name for f in source_csprojs]}"
            )

        # get rid of the path
        csproj_file_name = os.path.basename(source_csprojs[0].file_name)
        # get rid of .csproj
        csproj_file_name = csproj_file_name.replace(".csproj", "")
        # Load csproj template
        path = os.path.join("templates", "csharp", "TestProjectTemplate.csproj")
        try:
            with open(path, "r") as f:
                csproj_template = f.read()
        except Exception as e:
            raise Exception(f"Error loading file {path}: {e}")

        # create new csproj CodeFile
        self.dotnet_hardcoded_csproj_file = CodeFile(
            file_name=f"{csproj_file_name}-GSTests.csproj",
            source_code=csproj_template,
        )

    def post_process(self, code_project: CodeProject) -> CodeProject:
        # Make sure solutions have the same display_name as the source project
        # necessary so that the extension can find the correct project
        code_project.display_name = self.source_project.display_name

        if not self.use_dotnet_csproj:
            return code_project

        # First remove any existing csproj files
        code_project.files = [
            file for file in code_project.files if ".csproj" not in file.file_name
        ]
        # Then Add csproj file
        code_project.files.append(self.dotnet_hardcoded_csproj_file)

        return code_project

    def post_process_all(self, code_projects: list[CodeProject]) -> list[CodeProject]:
        """
        Post process a list of code projects
        :param code_projects: list of code projects to post process
        :return: list of post processed code projects
        """
        post_processed_projects: list[CodeProject] = []
        for project in code_projects:
            post_processed_projects.append(self.post_process(project))
        return post_processed_projects
