import json
import os
from datetime import datetime
from pprint import pprint

import pytest
from dapr.clients import DaprClient
from gs_common.CodeProject import CodeFile, CodeProject
from dataset.util import load_example_project

from src.goat_service.ut_generator.prompts.nunit_improve_ut_prompter import (
    NUnitImproveUTPrompter,
)
from src.goat_service.ut_generator.prompts.nunit_ut_prompter import (
    NUnitUTPrompter,
)
from src.goat_service.ut_generator.models.openai_ut_gen_llm import OpenAIUTGenLLM

MODEL = "gpt-4o-2024-05-13"
N_GENERATIONS = 5
TEMPERATURE = 0.2


def _save_all_test_projects(test_projects):
    # pprint(test_projects)
    print("len test_projects:", len(test_projects))
    assert test_projects != []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for i, test_project in enumerate(test_projects):
        test_project.save_to_dir(
            os.path.join("generated", f"test_ut_gen_llm_{timestamp}_{i}")
        )


def send_dapr(source_project=None, target_language=None):
    req_data = {}
    if source_project is not None:
        req_data["source_project"] = source_project.model_dump()
    if target_language is not None:
        req_data["target_language"] = target_language

    with DaprClient() as d:
        # Create a typed message with content type and body
        response = d.invoke_method(
            "goat_service",
            "pick_unittests",
            data=json.dumps(req_data),
            timeout=1000,
        )
    """
    if response.status_code == 200:
        pprint(response.json())
    else:
        print(response.status_code)
        print(response.text)
    """
    return response


def test_generate_unittests(
    project_name, project_type, relevant_public_functions, min_files=None
):
    source_project = load_example_project(project_name, project_type)
    llm = TestUTGenLLM(MODEL, N_GENERATIONS, TEMPERATURE)
    prompter = NUnitUTPrompter(source_project)
    test_projects = llm.generate_unittests(prompter)
    _save_all_test_projects(test_projects)

    count_good_projects = 0
    for test_project in test_projects:
        num_files = len(test_project.files)
        if min_files and num_files < min_files:
            print(f"min_files not met: {num_files} < {min_files}")
            continue
        source_code = "\n".join([f.source_code for f in test_project.files])
        # if not all(f in source_code for f in relevant_public_functions):
        included_functions = [f for f in relevant_public_functions if f in source_code]
        if not len(included_functions) == len(relevant_public_functions):
            print(
                f"missing functions: {included_functions} != {relevant_public_functions}"
            )
            continue
        num_tests = source_code.count("[Test]")
        if num_tests < len(relevant_public_functions) * 3:
            print(
                f"num_tests not met: {num_tests} < {len(relevant_public_functions) * 3}"
            )
            continue
        count_good_projects += 1

    print("count_good_projects:", count_good_projects)
    assert count_good_projects > N_GENERATIONS / 2


def test_generate_unittests_dotnetframework_dotnet8_json():
    test_generate_unittests(
        "Hashids.net-v112", "dotnetframework", ["CalculatePremium", "ProcessClaim"]
    )


def test_generate_unittests_dotnetframework_dotnet8_qrcoder():
    test_generate_unittests("QRCoder", "dotnetframework", ["CreateQrCode"], min_files=2)


def test_generate_unittests_dotnetframework_dotnet8_twofiles():
    test_generate_unittests(
        "TwoFiles", "dotnetframework", ["CalculatePremium", "ProcessClaim"], min_files=2
    )


def test_generate_unittests_dotnetframework_dotnet8_hashids():
    test_generate_unittests(
        "Hashids.net-v112", "dotnetframework", ["Encode", "Decode"], min_files=1
    )


def test_generate_unittests_dotnetframework_dotnet8_crc32():
    test_generate_unittests(
        "Crc32.NET-v100", "dotnetframework", ["Crc32Algorithm"], min_files=1
    )


def test_dotnetframework_hashids_fix_2bad():
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    old_test_project = load_example_project(
        "Hashids.net-v112-GSTests", "nunit_unittests_failed"
    )
    # remove test_results.xml from project and set as instruction
    results_file = next(
        (
            file
            for file in old_test_project.files
            if file.file_name == "test_results.xml"
        ),
        None,
    )
    if results_file is None:
        raise Exception("test_results.xml not found")
    old_test_project.files.remove(results_file)
    instruction = results_file.source_code
    print("old_test_project filenames:", [f.file_name for f in old_test_project.files])

    llm = TestUTGenLLM(MODEL, N_GENERATIONS, TEMPERATURE)
    prompter = NUnitImproveUTPrompter(source_project, instruction, old_test_project)
    new_test_projects = llm.generate_unittests(prompter)
    _save_all_test_projects(new_test_projects)

    # Assert
    # 1. should not be same as old test project
    # 2. should have same or more number of [Test]s
    # 3. should have same or more number of files
    # everything else is tested with test_workflow_generate_tests.py

    # old test project
    num_tests_old = 0
    for file in old_test_project.files:
        num_tests_old += file.source_code.count("[Test]")
    print("num_tests_old:", num_tests_old)
    num_files_old = len(old_test_project.files)
    print("num_files_old:", num_files_old)
    old_source_code = "\n".join([f.source_code for f in old_test_project.files])

    count_good_projects = 0
    for test_project in new_test_projects:
        num_files = len(test_project.files)
        if num_files < num_files_old:
            print(f"num_files not met: {num_files} < {num_files_old}")
            continue
        source_code = "\n".join([f.source_code for f in test_project.files])
        num_tests = source_code.count("[Test]")
        if num_tests < num_tests_old:
            print(f"num_tests not met: {num_tests} < {num_tests_old}")
            continue
        count_good_projects += 1
        assert source_code != old_source_code

    print("count_good_projects:", count_good_projects)
    assert count_good_projects > N_GENERATIONS / 2


if __name__ == "__main__":
    # pytest.main(["-vv", "-s", __file__])
    # test_generate_unittests_dotnetframework_dotnet8_json()
    # test_generate_unittests_dotnetframework_dotnet8_qrcoder()
    # test_generate_unittests_dotnetframework_dotnet8_qrcoder()
    # test_generate_unittests_dotnetframework_dotnet8_twofiles()
    # test_generate_unittests_dotnetframework_dotnet8_hashids()
    test_generate_unittests_dotnetframework_dotnet8_crc32()
