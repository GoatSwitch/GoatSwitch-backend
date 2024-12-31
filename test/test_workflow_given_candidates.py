import logging
import os
import time

import pytest
from gs_client import GSClient, GSClientResult
from gs_common.CodeProject import CodeFile, CodeProject

from dataset.util import load_example_project
from test.utils import MAX_WAIT_TIME, SERVER_URL

UT_GENERATIONS = 10
TL_GENERATIONS = 10

# setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def send_with_given_candidates(
    source_project: CodeProject,
    test_projects: list[CodeProject],
    tl_projects: list[CodeProject],
    target_language: str,
):
    gs_client = GSClient(
        server_url=SERVER_URL,
        max_wait_time=MAX_WAIT_TIME,
        project_name=source_project.display_name,
        run_id=os.getenv("RUN_ID", ""),
    )
    gs_client.connect()
    gs_client.send_workflow_given_candidates(
        source_project, test_projects, tl_projects, target_language
    )
    gs_client.disconnect()
    res: GSClientResult = gs_client.get_result()
    logging.info(f"res: {res}")

    assert (
        res.generate_unittests_state == "completed"
    ), f"bad generate_unittests_state ({res.generate_unittests_state}) for {res.trace_id}"
    assert (
        res.translate_state == "completed"
    ), f"bad translate_state ({res.translate_state}) for {res.trace_id}"
    assert (
        res.validate_state == "completed"
    ), f"bad validate_state ({res.validate_state}) for {res.trace_id}"
    assert res.timeout is False, f"bad timeout for {res.trace_id}"

    # parse ut solution
    if gs_client.ut_result is None or len(gs_client.ut_result) == 0:
        raise Exception(f"ut_result is None: {source_project.display_name}")
    if gs_client.ut_result[0]["solution"] is None:
        raise Exception(
            f"ut_result[0]['solution'] is None: {source_project.display_name}"
        )
    test_output = gs_client.ut_result[0]["test_output"]
    if test_output is not None and test_output != "":
        logging.info(f"test_output: {test_output.splitlines()[0]}")

    ut_solution = CodeProject.model_validate(gs_client.ut_result[0]["solution"])
    if ut_solution is None:
        raise Exception(f"ut_solution is None: {source_project.display_name}")

    # parse tl solution
    if gs_client.tl_result is None or len(gs_client.tl_result) == 0:
        raise Exception(f"tl_result is None: {source_project.display_name}")
    if gs_client.tl_result[0]["solution"] is None:
        raise Exception(
            f"tl_result[0]['solution'] is None: {source_project.display_name}"
        )
    tl_solution = CodeProject.model_validate(gs_client.tl_result[0]["solution"])
    if tl_solution is None:
        raise Exception(f"tl_solution is None: {source_project.display_name}")

    return res, ut_solution, tl_solution


@pytest.mark.parametrize(
    "program, source_language",
    [
        ("Hashids.net-v112", "dotnetframework"),
        ("Hashids.net-v112", "dotnet8"),
    ],
)
def test_dotnet8_success(program, source_language):
    source_project = load_example_project(program, source_language)
    test_project = load_example_project(program + "-GSTests", "nunit_unittests")
    tl_project = load_example_project(program, "dotnet8")

    res, ut_solution, tl_solution = send_with_given_candidates(
        source_project,
        [test_project] * UT_GENERATIONS,
        [tl_project] * TL_GENERATIONS,
        "dotnet8",
    )


@pytest.mark.parametrize(
    "program, source_language",
    [
        ("Hashids.net-v112", "dotnetframework"),
        ("Hashids.net-v112", "dotnet8"),
    ],
)
def test_dotnet8_bad_translation(program, source_language):
    source_project = load_example_project(program, source_language)
    test_project = load_example_project(program + "-GSTests", "nunit_unittests")
    tl_project = load_example_project(program, "dotnet8")
    # remove cs files from project
    tl_project.files = [f for f in tl_project.files if not f.file_name.endswith(".cs")]

    with pytest.raises(AssertionError):
        send_with_given_candidates(
            source_project,
            [test_project] * UT_GENERATIONS,
            [tl_project] * TL_GENERATIONS,
            "dotnet8",
        )


@pytest.mark.parametrize(
    "program, source_language",
    [
        ("spring-boot-payroll-example", "java8"),
    ],
)
def test_java21_success(program, source_language):
    source_project = load_example_project(program, source_language)
    test_project = load_example_project(program + "-GSTests", "junit_unittests")
    tl_project = load_example_project(program, "java21")

    res, ut_solution, tl_solution = send_with_given_candidates(
        source_project,
        [test_project] * UT_GENERATIONS,
        [tl_project] * TL_GENERATIONS,
        "java21",
    )


def debug():
    program = "AdonisUI"
    source_language = "dotnet8"
    source_dir = r"C:\mnt\gs-vault\2024-10-18\2689257253964dfb1b502861f8797b24\code_executor\18-10-36_82d6bcec8d6b11ef83dc00155d216e28\AdonisUI"
    test_dir = r"C:\mnt\gs-vault\2024-10-18\2689257253964dfb1b502861f8797b24\code_executor\18-10-36_82d6bcec8d6b11ef83dc00155d216e28\AdonisUI-GSTests"
    source_dir = source_dir.replace("\\", "/").replace("C:/mnt", "/mnt/c/mnt")
    test_dir = test_dir.replace("\\", "/").replace("C:/mnt", "/mnt/c/mnt")

    # for f in os.listdir(source_dir):
    #     print(f)
    source_project = CodeProject.load_from_dir(
        display_name=program, base_dir=source_dir, source_language=source_language
    )
    # print file names
    # for f in source_project.files:
    #     print(f.file_name)
    # exit()
    test_project = CodeProject.load_from_dir(
        display_name=program + "-GSTests",
        base_dir=test_dir,
        source_language="nunit_unittests",
    )
    tl_project = source_project

    res, ut_solution, tl_solution = send_with_given_candidates(
        source_project,
        [test_project] * UT_GENERATIONS,
        [tl_project] * TL_GENERATIONS,
        "gslite",
    )


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "--workers", "1"])
    # debug()
    # exit()

    for i in range(20):
        time.sleep(1)
        print("iter: ------------- ", i)
        # test_dotnet8_bad_translation("Hashids.net-v112", "dotnetframework")
        # test_dotnet8_success("Hashids.net-v112", "dotnetframework")
        test_dotnet8_success("Hashids.net-v112", "dotnet8")
        # test_vba_dotnet_success("HelloWorld", "vba")
        # test_java21_success("spring-boot-payroll-example", "java8")
        # test_java21_success("hql-criteria", "java21")
        exit()
