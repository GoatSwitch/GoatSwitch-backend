import os
import re
import uuid

from gs_common.CodeProject import CodeFile, CodeProject
from gs_common.tracing import current_company_id, current_trace_id, current_user_id

"""
Util methods to use the dataset projects for testing.
"""

DATASET_LANGUAGE_MAP = {
    "dotnetframework": [
        "dataset/demo-projects/DotNet-Framework",
    ],
    "dotnet8": [
        "dataset/private-projects/internal-testing/DotNet-8",
    ],
    "nunit_unittests": [
        "dataset/private-projects/internal-testing/DotNet-Framework",
        "dataset/private-projects/internal-testing/DotNet-8",
        "templates/csharp",
    ],
    "java8": [
        "dataset/demo-projects/Java8",
    ],
    "java21": [
        "dataset/demo-projects/Java21",
    ],
    "junit_unittests": [
        "dataset/private-projects/internal-testing/Java8",
        "dataset/private-projects/internal-testing/Java21",
    ],
}


def load_single_file(path, name, language) -> CodeProject:
    try:
        with open(os.path.join(path, name), "r") as f:
            source_code = f.read()
    # utf8 cant decode; try win 1250 for access
    except UnicodeDecodeError:
        try:
            with open(os.path.join(path, name), "r", encoding="windows-1250") as f:
                source_code = f.read()
        except Exception as e:
            raise Exception(f"could not read file: {name} error: {e}")
    return CodeProject(
        display_name=name,
        files=[CodeFile(file_name=name, source_code=source_code)],
        source_language=language,
    )


def load_example_project(name, language) -> CodeProject:
    # find the project in the dataset
    for path in DATASET_LANGUAGE_MAP[language]:
        project_dir = os.path.join(path, name)
        if os.path.exists(project_dir):
            break
    else:
        raise Exception(f"Project {name} not found for language {language}")

    # if single file, load it
    if os.path.isfile(project_dir):
        return load_single_file(
            os.path.dirname(project_dir), os.path.basename(project_dir), language
        )

    project = CodeProject.load_from_dir(
        display_name=name,
        base_dir=project_dir,
        source_language=language,
    )

    # NOTE: sort here so that .cs files are before .csproj files
    # to make it easy to modify source_files in tests by accessing files[0]
    project.files.sort(key=lambda x: x.file_name)
    return project


def remove_xml_style_comments(code: str) -> str:
    code = re.sub(r"///.*\n", "", code)
    return code


def remove_xml_style_comments_from_code_project(
    code_project: CodeProject,
) -> CodeProject:
    for code_file in code_project.files:
        if code_file.file_name.endswith(".cs"):
            code_file.source_code = remove_xml_style_comments(code_file.source_code)
    return code_project


def remove_java_style_comments(code: str) -> str:
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
    return code


def remove_java_style_comments_from_code_project(
    code_project: CodeProject,
) -> CodeProject:
    for code_file in code_project.files:
        if code_file.file_name.endswith(".java"):
            code_file.source_code = remove_java_style_comments(code_file.source_code)
    return code_project


def setup_trace_info_for_testing():
    current_trace_id.set(str(uuid.uuid4()))
    current_user_id.set("test_user")
    current_company_id.set("test_company")


def extract_maven_test_project(source_project: CodeProject) -> CodeProject:
    # set src/GSTests files as test project
    test_files = [
        f for f in source_project.files if f.file_name.startswith("src/GSTests")
    ]
    test_project = CodeProject(
        display_name=source_project.display_name + "-GSTests",
        source_language="java21",
        files=test_files,
    )
    # remove test files from source project
    src_files = [
        f for f in source_project.files if not f.file_name.startswith("src/GSTests")
    ]
    source_project.files = src_files
    return test_project
