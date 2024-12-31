import logging

from gs_common.CodeProject import CodeProject, ExecutionResult


class UTPicker:
    def __init__(self, source_project: CodeProject):
        self.source_project = source_project

    def pick_best(
        self,
        execution_results: list[ExecutionResult],
    ) -> ExecutionResult:
        """
        Pick the testsuite with the least failing tests and the most passing tests.
        """
        # sort by least failing tests and most passing tests
        execution_results.sort(
            key=lambda x: (x.failed_tests, -x.passed_tests), reverse=False
        )
        # log all
        for res in execution_results:
            logging.info(
                f"UTPicker: {res.project.display_name} has {res.failed_tests} failed tests and {res.passed_tests} passed tests"
            )
        # compute metrics should not raise exceptions
        try:
            self.compute_metrics(execution_results)
        except Exception as e:
            logging.error(f"Error in compute_metrics: {e}")

        return execution_results[0]

    def compute_metrics(self, execution_results: list[ExecutionResult]):
        # metrics for all test projects (including failed ones)
        n_test_projects = len(execution_results)
        logging.info(f"GSMETRIC:{n_test_projects=}")
        all_test_projects_avg_passed_tests = sum(
            [res.passed_tests for res in execution_results]
        ) / len(execution_results)
        logging.info(f"GSMETRIC:{all_test_projects_avg_passed_tests=}")
        all_test_projects_avg_failed_tests = sum(
            [res.failed_tests for res in execution_results]
        ) / len(execution_results)
        logging.info(f"GSMETRIC:{all_test_projects_avg_failed_tests=}")
        all_test_projects_avg_perc_passed_tests = round(
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
        logging.info(f"GSMETRIC:{all_test_projects_avg_perc_passed_tests=}")

        # metrics for best test project (can have failed)
        best_test_project_passed_tests = execution_results[0].passed_tests
        logging.info(f"GSMETRIC:{best_test_project_passed_tests=}")

        # metrics for all passed test projects (no failed tests)
        n_passed_test_projects = 0
        passed_test_projects_avg_passed_tests = 0
        for res in execution_results:
            if res.failed_tests == 0:
                n_passed_test_projects += 1
                passed_test_projects_avg_passed_tests += res.passed_tests
        if n_passed_test_projects > 0:
            passed_test_projects_avg_passed_tests = (
                passed_test_projects_avg_passed_tests / n_passed_test_projects
            )
        logging.info(f"GSMETRIC:{n_passed_test_projects=}")
        logging.info(f"GSMETRIC:{passed_test_projects_avg_passed_tests=}")
