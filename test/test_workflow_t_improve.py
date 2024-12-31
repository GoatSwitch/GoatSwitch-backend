import logging
import os
import time

from gs_client import GSClient, GSClientResult
from gs_common.CodeProject import CodeProject
from gs_common.proto.tl_picker_pb2 import ReturnCode

from dataset.util import (
    extract_maven_test_project,
    load_example_project,
    remove_java_style_comments_from_code_project,
    remove_xml_style_comments_from_code_project,
)
from test.utils import MAX_WAIT_TIME, SERVER_URL, print_diff

# setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def send_timprove(
    source_project: CodeProject,
    test_project: CodeProject,
    tl_project: CodeProject,
    instruction: str,
    target_language: str,
) -> CodeProject:
    gs_client = GSClient(
        server_url=SERVER_URL,
        max_wait_time=MAX_WAIT_TIME,
        project_name=source_project.display_name,
        run_id=os.getenv("RUN_ID", ""),
    )
    gs_client.connect()
    gs_client.send_workflow_improve_translation(
        source_project, test_project, tl_project, instruction, target_language
    )
    gs_client.disconnect()
    res: GSClientResult = gs_client.get_result()
    logging.info(f"res: {res}")

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


def test_comments_added():
    # Arrange
    program = "Hashids.net-v112"
    target_language = "dotnet8"
    source_project = load_example_project(program, "dotnetframework")
    test_project = load_example_project(program + "-GSTests", "nunit_unittests")
    tl_project = load_example_project(program, target_language)
    instruction = "Add XML style comments to every method"

    tl_project = remove_xml_style_comments_from_code_project(tl_project)
    # check that there are no comments
    comment_lines_old = 0
    for file in tl_project.files:
        # count lines with /// <summary> in the file
        comment_lines_old += len(
            [line for line in file.source_code.split("\n") if "/// <summary>" in line]
        )
    assert comment_lines_old == 0

    # Act
    res, ut_solution, tl_solution = send_timprove(
        source_project, test_project, tl_project, instruction, target_language
    )

    # Assert
    comment_lines_new = 0
    for file in tl_solution.files:
        # count lines with /// <summary> in the file
        comment_lines_new += len(
            [line for line in file.source_code.split("\n") if "/// <summary>" in line]
        )

    print(f"{comment_lines_new=}")
    assert comment_lines_new > 5


def test_logging_added():
    # Arrange
    program = "Hashids.net-v112"
    target_language = "dotnet8"
    source_project = load_example_project(program, "dotnetframework")
    test_project = load_example_project(program + "-GSTests", "nunit_unittests")
    tl_project = load_example_project(program, target_language)
    instruction = (
        "Add logging with log4net. Add a info log statement to one method in Hashids.cs"
    )

    res, ut_solution, tl_solution = send_timprove(
        source_project, test_project, tl_project, instruction, target_language
    )

    # check that there are more log statements
    log_lines = 0
    log_keywords = [".Info(", ".Debug(", ".Warn(", ".Error(", ".Fatal("]
    for file in tl_solution.files:
        # count lines with any of the log keywords in the file
        log_lines += len(
            [
                line
                for line in file.source_code.split("\n")
                if any(kw in line for kw in log_keywords)
            ]
        )

    print(f"New log lines: {log_lines}")
    assert log_lines > 0

    # check that log4net is imported in csproj file
    assert any(
        "log4net" in file.source_code
        for file in tl_solution.files
        if file.file_name.endswith(".csproj")
    )


def test_java21_docstrings_added():
    # Arrange
    # program = "spring-boot-payroll-example"
    program = "hql-criteria"
    target_language = "java21"
    source_project = load_example_project(program, "java21")
    test_project = load_example_project(program + "-GSTests", "junit_unittests")
    tl_project = load_example_project(program, target_language)
    instruction = "Add docstrings to non trivial methods"

    tl_project = remove_java_style_comments_from_code_project(tl_project)
    # check that there are no comments
    comment_lines_old = 0
    for file in tl_project.files:
        # count lines with /* in start of line in the file
        comment_lines_old += len(
            [
                line
                for line in file.source_code.split("\n")
                if line.strip().startswith("/*")
            ]
        )
    assert comment_lines_old == 0

    # Act
    res, ut_solution, tl_solution = send_timprove(
        source_project, test_project, tl_project, instruction, target_language
    )

    # Assert
    comment_lines_new = 0
    for file in tl_solution.files:
        # count lines with /* in start of line in the file
        comment_lines_new += len(
            [
                line
                for line in file.source_code.split("\n")
                if line.strip().startswith("/*")
            ]
        )
    print(f"{comment_lines_new=}")
    print_diff(tl_project, tl_solution)
    assert comment_lines_new > 1


def test_java21_criteria_added():
    # Arrange
    program = "hql-criteria"
    target_language = "java21"
    source_project = load_example_project(program, "java21")
    test_project = load_example_project(program + "-GSTests", "junit_unittests")
    tl_project = load_example_project(program, target_language)
    instruction = "Migrate from HQL to Criteria API"

    # Act
    res, ut_solution, tl_solution = send_timprove(
        source_project, test_project, tl_project, instruction, target_language
    )

    print_diff(tl_project, tl_solution)


def test_java21_criteria_added_with_tests():
    # Arrange
    program = "hql-criteria"
    target_language = "java21"
    source_project = load_example_project(program, "java21")
    tl_project = load_example_project(program, target_language)
    instruction = "Migrate from HQL to Criteria API"

    # Act
    res, ut_solution, tl_solution = send_timprove(
        source_project, None, tl_project, instruction, target_language
    )

    print_diff(tl_project, tl_solution)


def debug_from_convert():
    instruction = """\
        ['ngc'] error:

        STDOUT: 

        STDERR: src/app/app.component.html:10:89 - error TS2339: Property 'productCategory' does not exist on type 'AppComponent'.

        10             <input name="artikelart" type="radio" class="btn-check" id="bikes" [value]="productCategory.Bike"
                                                                                                ~~~~~~~~~~~~~~~

    """

    display_name = "defaultname"
    target_language = "dotnet"
    # load project
    dir = r"/mnt/gs-vault/2024-08-04/1c3ab8d8fc61a2d3fbccdc3c9bb7a332/code_executor/12-26-08_f6758fc0524b11ef909400155d70ac74/defaultname"
    tl_project = CodeProject.load_from_dir("defaultname", dir, target_language)
    logging.info(f"files: {[f.file_name for f in tl_project.files]}")

    source_project = CodeProject(
        display_name=display_name,
        files=[],
        source_language="dotnet",
    )
    test_project = source_project

    # Act
    res, ut_solution, tl_solution = send_timprove(
        source_project, test_project, tl_project, instruction, target_language
    )

    # Assert
    print_diff(tl_project, tl_solution)


def test_gslite_upgrade():
    # Arrange
    program = "Hashids.net-v112"
    target_language = "dotnet8"
    source_project = load_example_project(program, "dotnetframework")
    # tl_project = load_example_project(program, target_language)
    test_project = load_example_project("Dummy-GSTests", "nunit_unittests")
    instruction = "upgrade to dotnet8"

    # Act
    res, ut_solution, tl_solution = send_timprove(
        source_project, test_project, source_project, instruction, target_language
    )

    print_diff(source_project, tl_solution)


if __name__ == "__main__":
    # pytest.main([__file__, "-s", "--workers", "1"])

    # debug_from_convert()
    # exit()

    # test_java21_docstrings_added()
    # test_java21_criteria_added()
    # test_java21_criteria_added_with_tests()
    exit()

    for i in range(20):
        time.sleep(1)
        print("iter: ------------- ", i)
        # test_comments_added()
        test_logging_added()
        exit()
