import pytest
from gs_common.CodeProject import CodeFile, CodeProject, ExecutionResult

from dataset.util import load_example_project
from src.goat_service.ut_picker.ut_picker import UTPicker


def test_nunit_dotnet_one_testsuite_success():
    all_tests = [
        load_example_project("Hashids.net-v112-GSTests", "nunit_unittests"),
    ]
    result = ExecutionResult(
        project=load_example_project("Hashids.net-v112-GSTests", "nunit_unittests"),
        success=True,
        test_output="",
        failed_tests=0,
        total_tests=17,
        passed_tests=17,
    )
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    picker = UTPicker(source_project)

    best_result = picker.pick_best([result])

    assert all_tests[0].files[0].source_code == best_result.project.files[0].source_code


def test_nunit_dotnet_one_testsuite_one_failed():
    all_tests = [
        load_example_project("Hashids.net-v112-GSTests", "nunit_unittests"),
    ]
    result = ExecutionResult(
        project=all_tests[0],
        success=False,
        test_output="",
        failed_tests=1,
        total_tests=17,
        passed_tests=16,
    )
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    picker = UTPicker(source_project)

    best_result = picker.pick_best([result])

    assert all_tests[0].files[0].source_code == best_result.project.files[0].source_code
    assert best_result.failed_tests == 1


def test_nunit_dotnet_two_testsuites_success():
    all_tests = [
        load_example_project("Hashids.net-v112-GSTests", "nunit_unittests"),
        CodeProject(files=[CodeFile(file_name="EmptyTest.cs", source_code="")]),
    ]
    results = [
        ExecutionResult(
            project=all_tests[0],
            success=True,
            test_output="",
            failed_tests=0,
            total_tests=17,
            passed_tests=17,
        ),
        ExecutionResult(
            project=all_tests[1],
            success=True,
            test_output="",
            failed_tests=0,
            total_tests=17,
            passed_tests=17,
        ),
    ]

    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    picker = UTPicker(source_project)

    best_result = picker.pick_best(results)
    assert all_tests[0].files[0].source_code == best_result.project.files[0].source_code
    assert best_result.failed_tests == 0


def test_nunit_dotnet_two_testsuites_one_failed():
    all_tests = [
        load_example_project("Hashids.net-v112-GSTests", "nunit_unittests"),
        load_example_project("Hashids.net-v112-GSTests", "nunit_unittests"),
    ]
    results = [
        ExecutionResult(
            project=all_tests[0],
            success=False,
            test_output="",
            failed_tests=1,
            total_tests=27,
            passed_tests=26,
        ),
        ExecutionResult(
            project=all_tests[1],
            success=True,
            test_output="",
            failed_tests=0,
            total_tests=17,
            passed_tests=17,
        ),
    ]
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    picker = UTPicker(source_project)

    best_result = picker.pick_best(results)

    assert best_result.project.files[0].source_code == all_tests[1].files[0].source_code
    assert best_result.failed_tests == 0


def test_nunit_dotnet_two_testsuites_two_failed():
    all_tests = [
        load_example_project("Hashids.net-v112-GSTests", "nunit_unittests"),
        load_example_project("Hashids.net-v112-GSTests", "nunit_unittests"),
    ]
    results = [
        ExecutionResult(
            project=all_tests[0],
            success=False,
            test_output="",
            failed_tests=1,
            total_tests=17,
            passed_tests=13,
        ),
        ExecutionResult(
            project=all_tests[1],
            success=False,
            test_output="",
            failed_tests=1,
            total_tests=17,
            passed_tests=16,
        ),
    ]
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    picker = UTPicker(source_project)

    best_result = picker.pick_best(results)

    assert best_result.project.files[0].source_code == all_tests[1].files[0].source_code


def test_nunit_dotnet_dummytwo_testsuites_success():
    all_tests = [
        load_example_project("Hashids.net-v112-GSTests", "nunit_unittests"),
        CodeProject(files=[CodeFile(file_name="Hashids.cs", source_code="")]),
    ]
    results = [
        ExecutionResult(
            project=all_tests[0],
            success=True,
            test_output="",
            failed_tests=0,
            total_tests=17,
            passed_tests=17,
        ),
        ExecutionResult(
            project=all_tests[1],
            success=True,
            test_output="",
            failed_tests=0,
            total_tests=17,
            passed_tests=17,
        ),
    ]
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    picker = UTPicker(source_project)

    best_result = picker.pick_best(results)
    assert all_tests[0].files[0].source_code == best_result.project.files[0].source_code
    assert best_result.failed_tests == 0


def test_nunit_second_is_better():
    all_tests = [
        load_example_project("Hashids.net-v112-GSTests", "nunit_unittests"),
        load_example_project("Hashids.net-v112-GSTests", "nunit_unittests"),
    ]
    results = [
        ExecutionResult(
            project=all_tests[0],
            success=True,
            test_output="",
            failed_tests=0,
            total_tests=17,
            passed_tests=17,
        ),
        ExecutionResult(
            project=all_tests[1],
            success=True,
            test_output="",
            failed_tests=0,
            total_tests=27,
            passed_tests=27,
        ),
    ]
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    picker = UTPicker(source_project)

    best_result = picker.pick_best(results)
    assert all_tests[1].files[0].source_code == best_result.project.files[0].source_code
    assert best_result.failed_tests == 0


def test_junit_two_testsuites_one_failed():
    all_tests = [
        load_example_project("hql-criteria-GSTests", "junit_unittests"),
        load_example_project("hql-criteria-GSTests", "junit_unittests"),
    ]
    results = [
        ExecutionResult(
            project=all_tests[0],
            success=False,
            test_output="",
            failed_tests=1,
            total_tests=27,
            passed_tests=26,
        ),
        ExecutionResult(
            project=all_tests[1],
            success=True,
            test_output="",
            failed_tests=0,
            total_tests=17,
            passed_tests=17,
        ),
    ]
    source_project = load_example_project("hql-criteria", "java21")
    picker = UTPicker(source_project)

    best_result = picker.pick_best(results)

    assert best_result.project.files[0].source_code == all_tests[1].files[0].source_code
    assert best_result.failed_tests == 0


def test_junit_two_testsuites_two_failed():
    all_tests = [
        load_example_project("hql-criteria-GSTests", "junit_unittests"),
        load_example_project("hql-criteria-GSTests", "junit_unittests"),
    ]
    results = [
        ExecutionResult(
            project=all_tests[0],
            success=False,
            test_output="",
            failed_tests=1,
            total_tests=17,
            passed_tests=13,
        ),
        ExecutionResult(
            project=all_tests[1],
            success=False,
            test_output="",
            failed_tests=1,
            total_tests=17,
            passed_tests=16,
        ),
    ]
    source_project = load_example_project("hql-criteria", "java21")
    picker = UTPicker(source_project)

    best_result = picker.pick_best(results)

    assert best_result.project.files[0].source_code == all_tests[1].files[0].source_code


def test_junit_two_testsuites_one_failed_one_empty():
    all_tests = [
        load_example_project("hql-criteria-GSTests", "junit_unittests"),
        CodeProject(files=[CodeFile(file_name="EmptyTest.java", source_code="")]),
    ]
    results = [
        ExecutionResult(
            project=all_tests[0],
            success=False,
            test_output="",
            failed_tests=1,
            total_tests=27,
            passed_tests=26,
        ),
        ExecutionResult(
            project=all_tests[1],
            success=True,
            test_output="",
            failed_tests=0,
            total_tests=17,
            passed_tests=17,
        ),
    ]
    source_project = load_example_project("hql-criteria", "java21")
    picker = UTPicker(source_project)

    best_result = picker.pick_best(results)

    assert best_result.project.files[0].source_code == all_tests[1].files[0].source_code
    assert best_result.failed_tests == 0


def test_junit_second_is_better():
    all_tests = [
        load_example_project("hql-criteria-GSTests", "junit_unittests"),
        load_example_project("hql-criteria-GSTests", "junit_unittests"),
    ]
    results = [
        ExecutionResult(
            project=all_tests[0],
            success=True,
            test_output="",
            failed_tests=0,
            total_tests=17,
            passed_tests=17,
        ),
        ExecutionResult(
            project=all_tests[1],
            success=True,
            test_output="",
            failed_tests=0,
            total_tests=27,
            passed_tests=27,
        ),
    ]
    source_project = load_example_project("hql-criteria", "java21")
    picker = UTPicker(source_project)

    best_result = picker.pick_best(results)
    assert all_tests[1].files[0].source_code == best_result.project.files[0].source_code
    assert best_result.failed_tests == 0


if __name__ == "__main__":
    pytest.main(["-vv", "-s", __file__])
