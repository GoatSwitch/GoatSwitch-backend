from src.code_executor.dotnetframework_code_formatter import (
    DotnetFrameworkCodeFormatter,
)
from gs_common.CodeProject import CodeProject, CodeFile


def test_dotnetframework_code_formatter_packages_in_parent_dir():
    source_code = """<Project>
        <PropertyGroup>
        <TargetFrameworkVersion>v4.8</TargetFrameworkVersion>
        </PropertyGroup>
        <Reference Include=\"../packages/Newtonsoft.Json.12.0.3/lib/net45/Newtonsoft.Json.dll\" />
        </Project>"""
    project = CodeProject(
        files=[
            CodeFile(
                file_name="TestProject.csproj",
                source_code=source_code,
            )
        ]
    )
    formatted_project = DotnetFrameworkCodeFormatter.format(project)
    assert (
        '<Reference Include="packages/Newtonsoft.Json.12.0.3/lib/net45/Newtonsoft.Json.dll'
        in formatted_project.files[0].source_code
    )


def test_dotnetframework_code_formatter_no_change():
    source_code = """<Project>
        <PropertyGroup>
        <TargetFrameworkVersion>v4.8</TargetFrameworkVersion>
        </PropertyGroup>
        <Reference Include=\"packages/Newtonsoft.Json.12.0.3/lib/net45/Newtonsoft.Json.dll\" />
        </Project>"""
    project = CodeProject(
        files=[
            CodeFile(
                file_name="TestProject.csproj",
                source_code=source_code,
            )
        ]
    )
    formatted_project = DotnetFrameworkCodeFormatter.format(project)
    assert (
        '<Reference Include="packages/Newtonsoft.Json.12.0.3/lib/net45/Newtonsoft.Json.dll'
        in formatted_project.files[0].source_code
    )


def test_dotnetframework_code_formatter_packages_in_third_level_dir():
    source_code = """<Project>
        <PropertyGroup>
        <TargetFrameworkVersion>v4.8</TargetFrameworkVersion>
        </PropertyGroup>
        <Reference Include=\"../../../packages/Newtonsoft.Json.12.0.3/lib/net45/Newtonsoft.Json.dll\" />
        </Project>"""
    project = CodeProject(
        files=[
            CodeFile(
                file_name="TestProject.csproj",
                source_code=source_code,
            )
        ]
    )
    formatted_project = DotnetFrameworkCodeFormatter.format(project)
    assert (
        '<Reference Include="packages/Newtonsoft.Json.12.0.3/lib/net45/Newtonsoft.Json.dll'
        in formatted_project.files[0].source_code
    )


def test_qrcoder_old_framework_version_success():
    source_code = """<Project>
        <PropertyGroup>
        <TargetFrameworkVersion>v1.5</TargetFrameworkVersion>
        </PropertyGroup>
        <Reference Include=\"../../../packages/Newtonsoft.Json.12.0.3/lib/net45/Newtonsoft.Json.dll\" />
        </Project>"""
    project = CodeProject(
        files=[
            CodeFile(
                file_name="TestProject.csproj",
                source_code=source_code,
            )
        ]
    )
    formatted_project = DotnetFrameworkCodeFormatter.format(project)
    assert (
        "<TargetFrameworkVersion>v4.8</TargetFrameworkVersion>"
        in formatted_project.files[0].source_code
    )


def test_qrcoder_tricky_framework_version_success():
    source_code = """<Project>
        <PropertyGroup>
        <TargetFrameworkVersion>v2.8.1</TargetFrameworkVersion>
        </PropertyGroup>
        <Reference Include=\"../../../packages/Newtonsoft.Json.12.0.3/lib/net45/Newtonsoft.Json.dll\" />
        </Project>"""
    project = CodeProject(
        files=[
            CodeFile(
                file_name="TestProject.csproj",
                source_code=source_code,
            )
        ]
    )
    formatted_project = DotnetFrameworkCodeFormatter.format(project)
    assert (
        "<TargetFrameworkVersion>v4.8</TargetFrameworkVersion>"
        in formatted_project.files[0].source_code
    )


def test_qrcoder_missing_output_path():
    source_code = """<Project>
        <PropertyGroup>
        <TargetFrameworkVersion>v2.8.1</TargetFrameworkVersion>
        </PropertyGroup>
        <Reference Include=\"../../../packages/Newtonsoft.Json.12.0.3/lib/net45/Newtonsoft.Json.dll\" />
        </Project>"""
    project = CodeProject(
        files=[
            CodeFile(
                file_name="TestProject.csproj",
                source_code=source_code,
            )
        ]
    )
    formatted_project = DotnetFrameworkCodeFormatter.format(project)
    assert (
        "<OutputPath>bin\\Debug</OutputPath>" in formatted_project.files[0].source_code
    )
