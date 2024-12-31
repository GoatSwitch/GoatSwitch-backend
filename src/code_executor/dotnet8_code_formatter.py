import xml.etree.ElementTree as ET

from src.code_executor.code_formatter import CodeFormatter
from gs_common.CodeProject import CodeProject
from src.code_executor.dotnetframework_code_formatter import (
    DotnetFrameworkCodeFormatter,
)


class Dotnet8CodeFormatter(CodeFormatter):
    @staticmethod
    def format(project: CodeProject) -> CodeProject:
        csproj_file = DotnetFrameworkCodeFormatter.get_main_csproj_file(project)
        root = DotnetFrameworkCodeFormatter.read_and_format_csproj_file(csproj_file)
        DotnetFrameworkCodeFormatter.set_internals_visible_to_testproject(
            project, root, csproj_file.file_name
        )
        DotnetFrameworkCodeFormatter.disable_sign_assembly(root)
        csproj_file.source_code = ET.tostring(root, encoding="unicode")
        csproj_file.file_name = DotnetFrameworkCodeFormatter.remove_ico_references(
            csproj_file.file_name
        )
        return project
