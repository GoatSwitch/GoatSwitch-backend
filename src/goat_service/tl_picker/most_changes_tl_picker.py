import logging
import difflib

from gs_common.CodeProject import CodeProject, ExecutionResult

from src.goat_service.tl_picker.tl_picker import TLPicker


class MostChangesTLPicker(TLPicker):
    """
    Prioritize the project with the most changes to the source project.
    But also penalizes projects with failed tests.
    """

    def compute_score(self, execution_result: ExecutionResult) -> int:
        try:
            n_changes = self.get_n_changes(execution_result.project)
        except Exception as e:
            logging.error(f"Failed to get changes: {e}")
            n_changes = -1
        score = n_changes
        logging.info(f"n_changes: {n_changes}")
        # give a huge penalty for failed tests -> to always prioritize low number of failed tests
        score -= 1000 * execution_result.failed_tests
        logging.info(
            f"TLPicker Score: {score} for project {execution_result.project.display_name}"
        )
        return score

    def get_n_changes(self, project: CodeProject) -> int:
        # calc n changes between source and project
        n_changes = 0
        n_changed_files = 0
        for file in project.files:
            old_file = self.source_project.get_file(file.file_name)
            if old_file is None:
                # new file add all lines
                diff = [f"+ {line}" for line in file.source_code.split("\n")]
            else:
                diff = difflib.unified_diff(
                    old_file.source_code.split("\n"),
                    file.source_code.split("\n"),
                    lineterm="",
                )

                # continue if there is no diff
                diff = list(diff)
                if not diff:
                    continue

            n_changes += len(diff)
            n_changed_files += 1

        return n_changes
