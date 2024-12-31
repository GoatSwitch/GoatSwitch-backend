import logging

from gs_common.CodeProject import CodeProject, ExecutionResult


class TLPicker:
    def __init__(self, source_project: CodeProject):
        self.source_project = source_project

    def pick_best(
        self,
        execution_results: list[ExecutionResult],
    ) -> ExecutionResult:
        """
        Pick the result with the highest score.
        """
        # sort by score
        execution_results.sort(key=lambda x: self.compute_score(x), reverse=True)
        # compute metrics should not raise exceptions
        try:
            self.compute_metrics(execution_results)
        except Exception as e:
            logging.error(f"Error in compute_metrics: {e}")
        return execution_results[0]

    def compute_score(self, execution_result: ExecutionResult) -> int:
        # default: score is negative number of failed tests
        score = -execution_result.failed_tests
        logging.info(
            f"TLPicker Score: {score} for project {execution_result.project.display_name}"
        )
        return score

    def compute_metrics(self, execution_results: list[ExecutionResult]):
        # metrics for all tl projects (including failed ones)
        n_tl_projects = len(execution_results)
        logging.info(f"GSMETRIC:{n_tl_projects=}")
        all_tl_projects_avg_passed_tests = sum(
            [res.passed_tests for res in execution_results]
        ) / len(execution_results)
        logging.info(f"GSMETRIC:{all_tl_projects_avg_passed_tests=}")
        all_tl_projects_avg_failed_tests = sum(
            [res.failed_tests for res in execution_results]
        ) / len(execution_results)
        logging.info(f"GSMETRIC:{all_tl_projects_avg_failed_tests=}")
        all_tl_projects_avg_perc_passed_tests = round(
            sum(
                [
                    res.passed_tests / res.total_tests if res.total_tests != 0 else 0
                    for res in execution_results
                ]
            )
            / len(execution_results)
            * 100,
            2,
        )
        logging.info(f"GSMETRIC:{all_tl_projects_avg_perc_passed_tests=}")

        # metrics for best tl project (can have failed)
        best_tl_project_passed_tests = execution_results[0].passed_tests
        logging.info(f"GSMETRIC:{best_tl_project_passed_tests=}")

        # metrics for all passed tl projects (no failed tests)
        n_passed_tl_projects = len(
            [res for res in execution_results if res.failed_tests == 0]
        )
        logging.info(f"GSMETRIC:{n_passed_tl_projects=}")
