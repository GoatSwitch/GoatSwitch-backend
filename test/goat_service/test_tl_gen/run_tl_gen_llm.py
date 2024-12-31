import os
from datetime import datetime

import pytest
from gs_common.CodeProject import CodeProject
from dataset.util import (
    load_example_project,
    remove_xml_style_comments_from_code_project,
)

from src.goat_service.tl_generator.models.openai_tl_gen_llm import (
    OpenAITLGenLLM,
)
from src.goat_service.tl_generator.prompts.dotnet8_improve_tl_prompter import (
    DotNet8ImproveTLPrompter,
)
from src.goat_service.tl_generator.prompts.dotnetframework_dotnet8_tl_prompter import (
    DotNetFrameworkDotNet8TLPrompter,
)

# MODEL = "code-bison"
# MODEL = "gpt-3.5-turbo-0125"
MODEL = "gpt-4o-2024-05-13"
TestTLGenLLM = OpenAITLGenLLM
N_GENERATIONS = 10
TRANSLATION_TEMPERATURE = 0.3


def count_solutions_with_function_definition(
    translated_projects: list[CodeProject],
    function_definition,
    print_definitions_starting_with=None,
):
    count = 0
    for translated_project in translated_projects:
        print("-" * 80)
        if print_definitions_starting_with is not None:
            lines = translated_project.files[0].source_code.split("\n")
            print_lines = [
                line
                for line in lines
                if print_definitions_starting_with in line.lower()
            ]
            print("\n".join(print_lines))

        if (
            function_definition.lower()
            in translated_project.files[0].source_code.lower()
        ):
            count += 1
    print("count", count)
    return count


def test_trans_dotnetframework_dotnet8_json():
    llm = TestTLGenLLM(MODEL, N_GENERATIONS, TRANSLATION_TEMPERATURE)
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    prompter = DotNetFrameworkDotNet8TLPrompter(source_project)

    translated_projects = llm.generate_translations(prompter)

    assert translated_projects != []

    # .Serialize method is new in .net8
    count = count_solutions_with_function_definition(
        translated_projects, ".Serialize(", ".Serialize("
    )
    assert count > 0


def test_trans_dotnetframework_dotnet8_json_with_reference_files():
    llm = TestTLGenLLM(MODEL, N_GENERATIONS, TRANSLATION_TEMPERATURE)
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    # add useless reference files
    qrcoder = load_example_project("QRCoder", "dotnetframework")
    source_project.reference_files = qrcoder.files
    # TODO: deprecated; we don't use gpt3.5 anymore
    # add one more time to go over gpt3.5 token limit
    source_project.reference_files += qrcoder.files

    prompter = DotNetFrameworkDotNet8TLPrompter(source_project)

    translated_projects = llm.generate_translations(prompter)

    assert translated_projects != []

    # .Serialize method is new in .net8
    count = count_solutions_with_function_definition(
        translated_projects, ".Serialize(", ".Serialize("
    )
    assert count > 0


def helper_add_docstrings(project_name, file_name, min_summary_count):
    llm = TestTLGenLLM(MODEL, N_GENERATIONS, TRANSLATION_TEMPERATURE)
    source_project = load_example_project(project_name, "dotnet8")
    source_project = remove_xml_style_comments_from_code_project(source_project)
    instruction = "Add a XML style docstring to each public method."
    prompter = DotNet8ImproveTLPrompter(source_project, instruction)

    translated_projects: list[CodeProject] = llm.generate_translations(prompter)

    # save for debugging
    for i, translated in enumerate(translated_projects):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        translated.save_to_dir(
            os.path.join(
                "generated", f"test_{project_name}_add_docstrings_{timestamp}_{i}"
            )
        )

    assert translated_projects != []

    # two important criteria for a translation to count as good
    # 1. file_name must have at least the same line count
    # 2. file_name must have at least min_summary_count /// <summary> tags
    orig_line_count = 0
    for file in source_project.files:
        if file.file_name == file_name:
            orig_line_count = len(file.source_code.split("\n"))
            break

    n_passed = 0
    for i, translated_project in enumerate(translated_projects):
        for file in translated_project.files:
            if file.file_name == file_name:
                line_count = len(file.source_code.split("\n"))
                summary_count = file.source_code.count("/// <summary>")
                if line_count >= orig_line_count:
                    if summary_count >= min_summary_count:
                        n_passed += 1
                    else:
                        print(
                            f"Project {i} failed due to insufficient summary count: {summary_count}"
                        )
                else:
                    print(
                        f"Project {i} failed due to insufficient line count: {line_count}"
                    )
                break

    print(f"n_passed: {n_passed}")
    assert (
        n_passed >= N_GENERATIONS / 2
    ), f"n_passed: {n_passed}; n_translations: {len(translated_projects)}"


def test_dotnet8_qrcoder_add_docstrings():
    # NOTE: more than 5 possible; but gpt does not always comment all functions
    helper_add_docstrings("QRCoder", "QRCode.cs", 5)


def test_dotnet8_hashids_add_docstrings():
    helper_add_docstrings("Hashids.net-v112", "Hashids.cs", 5)


def helper_rename_variable(project_name, file_name, old_var_name, new_var_name):
    llm = TestTLGenLLM(MODEL, N_GENERATIONS, TRANSLATION_TEMPERATURE)
    source_project = load_example_project(project_name, "dotnet8")
    source_project = remove_xml_style_comments_from_code_project(source_project)
    instruction = f"Rename variable '{old_var_name}' to '{new_var_name}'."
    prompter = DotNet8ImproveTLPrompter(source_project, instruction)

    translated_projects: list[CodeProject] = llm.generate_translations(prompter)

    # save for debugging
    for i, translated in enumerate(translated_projects):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        translated.save_to_dir(
            os.path.join(
                "generated", f"test_{project_name}_rename_variable_{timestamp}_{i}"
            )
        )

    assert translated_projects != []

    # two important criteria for a translation to count as good
    # 1. file must have at least the same line count
    # 2. all instances must be renamed
    orig_line_count = 0
    for file in source_project.files:
        if file.file_name == file_name:
            orig_line_count = len(file.source_code.split("\n"))
            break

    n_passed = 0
    for i, translated_project in enumerate(translated_projects):
        for file in translated_project.files:
            if file.file_name == file_name:
                line_count = len(file.source_code.split("\n"))
                if line_count >= orig_line_count:
                    if old_var_name not in file.source_code:
                        if new_var_name in file.source_code:
                            n_passed += 1
                        else:
                            print(f"Project {i} failed due to missing '{new_var_name}'")
                    else:
                        print(f"Project {i} failed due to presence of '{old_var_name}'")
                else:
                    print(
                        f"Project {i} failed due to insufficient line count: {line_count}"
                    )
                break

    print(f"n_passed: {n_passed}")
    assert (
        n_passed >= N_GENERATIONS / 2
    ), f"n_passed: {n_passed}; n_translations: {len(translated_projects)}"


def test_dotnet8_hashids_rename_variable():
    helper_rename_variable(
        "Hashids.net-v112", "Hashids.cs", "DEFAULT_ALPHABET", "DEF_ALPHABET"
    )


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
    # test_trans_dotnetframework_dotnet8_json()
