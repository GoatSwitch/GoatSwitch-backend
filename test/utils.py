import difflib
import os

from gs_client import GSClientResult
from gs_common.CodeProject import CodeProject

from dataset.util import DATASET_LANGUAGE_MAP

MAX_WAIT_TIME = 500
# SERVER_URL = "http://localhost:5000"
SERVER_URL = "https://api.goatswitch.ai"


def get_dataset(language):
    projects = []
    folders = DATASET_LANGUAGE_MAP[language]
    for folder in folders:
        for project_name in os.listdir(folder):
            if project_name.endswith(".sln"):
                continue
            # skip tests
            if "-GSTests" in project_name:
                continue
            # NOTE: very large form
            if project_name == "frmEinkaufsbestellung_Zeilen.txt":
                continue
            # NOTE: very large form
            if project_name == "frmEinkaufsbestellung.txt":
                continue
            # NOTE: DesignPatterns contains multiple projects; only take first for now
            if project_name == "DesignPatterns":
                project_name = "DesignPatterns/AdapterPattern"
            projects.append(project_name)
    return projects


def print_diff(project_before: CodeProject, project_after: CodeProject) -> list[str]:
    """
    Print diff between two projects
    Returns list of filenames that have changed or are new
    """
    # n files before
    print(f"Number of files before: {len(project_before.files)}")
    # n files after
    print(f"Number of files after: {len(project_after.files)}")
    lines_added = 0
    lines_removed = 0
    lines_changed = 0
    files_changed = []
    for file in project_before.files:
        improved_file = project_after.get_file(file.file_name)
        if improved_file is None:
            print(f"improved file not found: {file.file_name}")
            continue

        diff = difflib.unified_diff(
            file.source_code.split("\n"),
            improved_file.source_code.split("\n"),
            lineterm="",
        )
        diff_list = list(diff)
        if not diff_list:
            # print(f"No diff for file: {file.file_name}")
            continue

        print(f">>>> Diff for file: {file.file_name}")
        for line in diff_list:
            print(line)
            if line.startswith("+"):
                lines_added += 1
            elif line.startswith("-"):
                lines_removed += 1
            elif line.startswith("@@"):
                lines_changed += 1
        files_changed.append(file.file_name)

    # print new files filenames and content
    new_files = []
    for file in project_after.files:
        if project_before.get_file(file.file_name) is None:
            # skip diff.txt from op_applier
            if file.file_name == "diff.txt":
                continue
            if file.file_name == "operations.txt":
                continue
            print(f"New file: {file.file_name}")
            print(file.source_code)
            new_files.append(file.file_name)

    # overview of changes
    print(f"Number of files: {len(project_before.files)}")
    print(f"Number of files changed: {len(files_changed)}")
    print(f"Number of lines added: {lines_added}")
    print(f"Number of lines removed: {lines_removed}")
    print(f"Number of lines changed: {lines_changed}")
    print(f"Number of new files: {len(new_files)}")

    return files_changed + new_files


def assert_basics(
    res: GSClientResult, ut_solution: CodeProject, tl_solution: CodeProject
):
    assert_basics_ut_result(res, ut_solution)
    assert_basics_tl_result(res, tl_solution)


def assert_basics_ut_result(res: GSClientResult, ut_solution: CodeProject):
    # log trace_id in case of failure
    assert (
        res.generate_unittests_state == "completed"
    ), f"bad generate_unittests_state ({res.generate_unittests_state}) for {res.trace_id}"
    assert (
        res.validate_state == "completed"
    ), f"bad validate_state ({res.validate_state}) for {res.trace_id}"
    assert res.timeout is False, f"bad timeout for {res.trace_id}"
    assert ut_solution is not None, f"no ut solution for {res.trace_id}"
    assert len(ut_solution.files) > 0, f"no files in ut solution for {res.trace_id}"


def assert_basics_tl_result(res: GSClientResult, tl_solution: CodeProject):
    # log trace_id in case
    assert (
        res.translate_state == "completed"
    ), f"bad translate_state ({res.translate_state}) for {res.trace_id}"
    assert (
        res.validate_state == "completed"
    ), f"bad validate_state ({res.validate_state}) for {res.trace_id}"
    assert res.timeout is False, f"bad timeout for {res.trace_id}"
    assert tl_solution is not None, f"no tl solution for {res.trace_id}"
    assert len(tl_solution.files) > 0, f"no files in tl solution for {res.trace_id}"
