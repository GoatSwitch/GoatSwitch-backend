import pytest
from gs_common.CodeProject import CodeFile, CodeProject, ExecutionResult

from dataset.util import load_example_project
from src.goat_service.tl_picker.tl_picker import TLPicker


def test_default_second_better_score():
    all_projects = [
        load_example_project("Hashids.net-v112", "dotnet8"),
        load_example_project("Hashids.net-v112", "dotnet8"),
    ]

    all_projects[0].files[0].source_code = "source_code"
    all_results = [
        ExecutionResult(all_projects[0], success=True, test_output="", failed_tests=1),
        ExecutionResult(all_projects[1], success=True, test_output="", failed_tests=0),
    ]
    source_project = (load_example_project("Hashids.net-v112", "dotnetframework"),)
    picker = TLPicker(source_project)
    best_result = picker.pick_best(all_results)
    assert best_result.failed_tests == 0
    assert (
        best_result.project.files[0].source_code == all_projects[1].files[0].source_code
    )
