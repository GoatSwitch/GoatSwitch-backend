import logging

import pytest
from gs_common.CodeProject import CodeProject

from dataset.util import (
    extract_maven_test_project,
    load_example_project,
)
from test.test_workflow_convert import send_convert
from test.test_workflow_execute_plan import send_execute_plan
from test.test_workflow_gen_plan import send_gen_plan
from test.test_workflow_given_candidates import send_with_given_candidates
from test.test_workflow_t_improve import send_timprove
from test.utils import assert_basics, get_dataset


@pytest.mark.parametrize("project_name", get_dataset("java8"))
def test_java8_to_java21(project_name):
    source_project = load_example_project(project_name, "java8")
    res, ut_solution, tl_solution = send_convert(
        source_project,
        target_language="java21",
    )
    assert_basics(res, ut_solution, tl_solution)


@pytest.mark.parametrize("project_name", get_dataset("java21"))
def test_java21_timprove(project_name):
    source_project = load_example_project(project_name, "java21")
    if "hql" in project_name:
        instruction = "Migrate from HQL to Criteria API"
        test_project = None
    else:
        # do not test this
        logging.info(f"Skipping {project_name} for test_java21_timprove")
        return

    res, ut_solution, tl_solution = send_timprove(
        source_project=source_project,
        test_project=test_project,
        tl_project=source_project,
        instruction=instruction,
        target_language="java21",
    )
    assert_basics(res, ut_solution, tl_solution)


@pytest.mark.parametrize("project_name", get_dataset("dotnetframework"))
def test_dotnet_framework_to_dotnet8(project_name):
    source_project = load_example_project(project_name, "dotnetframework")
    # asp.net projects cannot be migrated one shot; do not test them here
    csproj = [f for f in source_project.files if f.file_name.endswith(".csproj")][0]
    if "System.Web" in csproj.source_code:
        logging.info(f"Skipping {project_name} for test_dotnet_framework_to_dotnet8")
        return

    res, ut_solution, tl_solution = send_convert(
        source_project,
        target_language="dotnet8",
    )
    assert_basics(res, ut_solution, tl_solution)


@pytest.mark.parametrize("project_name", get_dataset("dotnetframework"))
def test_gslite_dotnet(project_name: str):
    source_language = "dotnetframework"
    source_project = load_example_project(project_name, source_language)
    # asp.net projects cannot be migrated one shot; do not test them here
    csproj = [f for f in source_project.files if f.file_name.endswith(".csproj")][0]
    if "System.Web" in csproj.source_code:
        logging.info(f"Skipping {project_name} for test_dotnet_framework_to_dotnet8")
        return
    instruction = "upgrade to dotnet8 and add one docstring"

    # gen plan
    res, instruction = send_gen_plan(source_project, instruction)

    # execute plan
    res, ut_solution, tl_solution = send_execute_plan(source_project, instruction)

    # use WorkflowWithGivenCandidates to verify tl_solution
    test_project = load_example_project("Dummy-GSTests", "nunit_unittests")
    res, ut_solution, tl_solution = send_with_given_candidates(
        source_project, [test_project], [tl_solution], "dotnet8"
    )
    assert_basics(res, ut_solution, tl_solution)


@pytest.mark.parametrize("project_name", get_dataset("dotnetframework"))
def test_gslite_aspnet(project_name: str):
    if "OrderTrackingDashboard" not in project_name:
        # do not test this
        logging.info(f"Skipping {project_name} for test_gslite_aspnet")
        return
    source_language = "dotnetframework"
    source_project = load_example_project(project_name, source_language)
    instruction = "upgrade to asp.net core and net8"

    # log file names
    logging.info(
        f"Source project filenames: {[f.file_name for f in source_project.files]}"
    )

    # gen plan
    res, instruction = send_gen_plan(source_project, instruction)

    # execute plan
    res, ut_solution, tl_solution = send_execute_plan(source_project, instruction)

    # use WorkflowWithGivenCandidates to verify tl_solution
    test_project = load_example_project("Dummy-GSTests", "nunit_unittests")
    res, ut_solution, tl_solution = send_with_given_candidates(
        source_project, [test_project], [tl_solution], "dotnet8"
    )
    assert_basics(res, ut_solution, tl_solution)


if __name__ == "__main__":
    pytest.main([__file__, "-s", "-n", "4"])
    # test_java8_to_java21("spring-boot-payroll-example")
    # test_java21_timprove("hql-criteria")
