import logging
import os
from textwrap import dedent

import pytest
from gs_client import GSClient, GSClientResult
from gs_common.CodeProject import CodeProject

from dataset.util import load_example_project
from src.goat_service.tl_generator.prompts.universal_plan_prompter import AIPlan
from test.test_workflow_gen_plan import send_gen_plan
from test.test_workflow_given_candidates import send_with_given_candidates
from test.utils import (
    MAX_WAIT_TIME,
    SERVER_URL,
    assert_basics,
    assert_basics_tl_result,
    get_dataset,
    print_diff,
)

# setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def send_execute_plan(
    source_project: CodeProject,
    instruction: str,
):
    gs_client = GSClient(
        server_url=SERVER_URL,
        max_wait_time=MAX_WAIT_TIME,
        project_name=source_project.display_name,
        run_id=os.getenv("RUN_ID", ""),
    )

    gs_client.connect()
    gs_client.send_workflow_execute_plan(source_project, instruction)
    gs_client.disconnect()
    res: GSClientResult = gs_client.get_result()
    logging.info(f"res: {res}")
    if res.translate_error:
        raise Exception(f"translate_error: {res.translate_error}")
    if res.generate_unittests_error:
        raise Exception(f"translate_error: {res.translate_error}")
    if res.validate_error:
        # NOTE: validate error can also be "workflow completed, but some steps failed" (see gs_client.py)
        raise Exception(f"validate_error: {res.validate_error}")

    # NOTE: depending on the plan, it is valid to only change the source project or test project
    # as long as we can parse one of the solutions, we are good

    # parse ut solution
    try:
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
    except Exception as e:
        logging.info(f"exec plan: cannot parse ut solution: {e}")
        ut_solution = None

    try:
        # parse tl project
        if gs_client.tl_result is None or len(gs_client.tl_result) == 0:
            raise Exception(f"tl_result is None: {source_project.display_name}")
        if gs_client.tl_result[0]["solution"] is None:
            raise Exception(
                f"tl_result[0]['solution'] is None: {source_project.display_name}"
            )
        tl_solution = CodeProject.model_validate(gs_client.tl_result[0]["solution"])
        if tl_solution is None:
            raise Exception(f"tl_solution is None: {source_project.display_name}")
    except Exception as e:
        logging.info(f"exec plan: cannot parse tl solution: {e}")
        tl_solution = None

    if ut_solution is None and tl_solution is None:
        raise Exception("exec plan: both ut and tl solutions are None")

    # NOTE: if ut_solution is None, we can still continue with tl_solution
    # NOTE: but if tl_solution is None, we should use source_project
    if tl_solution is None:
        tl_solution = source_project

    return res, ut_solution, tl_solution


@pytest.mark.parametrize("project_name", get_dataset("dotnetframework"))
def test_execute_plan_upgrade_dotnet8(project_name: str):
    source_language = "dotnetframework"
    source_project = load_example_project(project_name, source_language)

    # instruction = "upgrade to dotnet8 and add serilog and 3 logging statements"
    instruction = "upgrade asp.net to asp.net core and net8; do not generate tests"
    res, instruction = send_gen_plan(source_project, instruction)

    # instruction = dedent("""\
    # # AI Plan
    # ## Step 1: upgrade dotnet project
    # Upgrade the project from .NET Framework to .NET 8. This involves updating the project file to the new SDK-style format and changing the TargetFramework to net8.0.
    # ## Step 2: integrate serilog
    # Add Serilog as a logging library to the project. This involves adding the Serilog NuGet package and configuring it in the project.
    # ## Step 3: add 3 logging statements
    # Add three logging statements using Serilog in the Hashids class. These statements should log key operations.
    # """)

    res, ut_solution, tl_solution = send_execute_plan(source_project, instruction)

    # use WorkflowWithGivenCandidates to verify tl_solution
    test_project = load_example_project("Dummy-GSTests", "nunit_unittests")
    res, _, tl_solution = send_with_given_candidates(
        source_project, [test_project], [tl_solution], "dotnet8"
    )
    # save to file
    tl_solution.save_to_dir("/home/mw3155/tmp/test_workflow_execute_plan")

    # get diff
    changed_files = print_diff(source_project, tl_solution)

    assert_basics_tl_result(res, tl_solution)


@pytest.mark.parametrize("project_name", get_dataset("dotnetframework"))
def test_execute_plan_generate_tests(project_name: str):
    source_language = "dotnetframework"
    source_project = load_example_project(project_name, source_language)

    # instruction = "generate tests"
    # instruction = "upgrade and generate 2 tests"
    instruction = "generate 1 test"
    res, instruction = send_gen_plan(source_project, instruction)

    # instruction = dedent("""\
    # # AI Plan
    # ## Step 1: upgrade dotnet project
    # Upgrade the project from .NET Framework to .NET 8. This involves updating the project file to the new SDK-style format and changing the TargetFramework to net8.0.
    # ## Step 2: integrate serilog
    # Add Serilog as a logging library to the project. This involves adding the Serilog NuGet package and configuring it in the project.
    # ## Step 3: add 3 logging statements
    # Add three logging statements using Serilog in the Hashids class. These statements should log key operations.
    # """)

    res, ut_solution, tl_solution = send_execute_plan(source_project, instruction)
    # use WorkflowWithGivenCandidates to verify tl_solution
    res, ut_solution, tl_solution = send_with_given_candidates(
        source_project, [ut_solution], [tl_solution], tl_solution.source_language
    )
    # save to file
    ut_solution.save_to_dir("/home/mw3155/tmp/test_workflow_execute_plan_gen_tests")

    assert_basics(res, ut_solution, tl_solution)
