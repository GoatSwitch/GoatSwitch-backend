from gs_common.CodeProject import CodeFile, CodeProject, ExecutionResult

from dataset.util import load_example_project
from src.goat_service.tl_picker.most_changes_tl_picker import MostChangesTLPicker


def test_dotnet_second_more_changes():
    all_projects = [
        load_example_project("Hashids.net-v112", "dotnet8"),
        load_example_project("Hashids.net-v112", "dotnet8"),
    ]
    source_project = load_example_project("Hashids.net-v112", "dotnetframework")
    # modify second one to have more changes (add file)
    all_projects[1].files.append(CodeFile(file_name="new_file.txt", source_code="new"))
    all_results = [
        ExecutionResult(all_projects[0], success=True, test_output="", failed_tests=1),
        ExecutionResult(all_projects[1], success=True, test_output="", failed_tests=1),
    ]
    picker = MostChangesTLPicker(source_project)
    best_result = picker.pick_best(all_results)
    assert best_result.failed_tests == 1
    assert best_result.project.files[-1].source_code == "new"
