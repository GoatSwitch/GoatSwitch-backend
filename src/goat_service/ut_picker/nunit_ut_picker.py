import logging
import re

from gs_common.CodeProject import CodeProject, ExecutionResult

from src.goat_service.ut_picker.ut_picker import UTPicker


class NUnitUTPicker(UTPicker):
    def __init__(self, source_project: CodeProject = None):
        self.source_project = source_project
        # search for "public/internal class " in source_code
        self.class_names_to_test = set()
        for file in self.source_project.files:
            try:
                class_names = re.findall(r"public class (\w+)", file.source_code)
                self.class_names_to_test.update(class_names)
                class_names = re.findall(r"internal class (\w+)", file.source_code)
                self.class_names_to_test.update(class_names)
            except Exception:
                logging.error(f"Error in regex: {file.source_code}")

    def compute_metrics(self, execution_results: list[ExecutionResult]):
        # compute basic metrics
        super().compute_metrics(execution_results)

        # compute NUnit specific metrics
        best_test_project_classes_tested = self.get_metric_perc_classes_tested(
            execution_results[0].project
        )
        logging.info(f"GSMETRIC:{best_test_project_classes_tested=}")

        best_test_project_useful_asserts = self.get_metric_perc_useful_asserts(
            execution_results[0].project
        )
        logging.info(f"GSMETRIC:{best_test_project_useful_asserts=}")

    def get_metric_perc_classes_tested(self, project: CodeProject):
        if len(self.class_names_to_test) == 0:
            return 0
        # search for "new {class_name}(" in source_code
        class_names_tested = set()
        for file in project.files:
            for class_name in self.class_names_to_test:
                try:
                    found = re.findall(rf"new {class_name}\(", file.source_code)
                    class_names_tested.update(found)
                except Exception:
                    logging.error(f"Error in regex: {class_name}")
        return round(len(class_names_tested) / len(self.class_names_to_test) * 100, 2)

    def get_metric_perc_useful_asserts(self, project: CodeProject):
        # NOTE: this is a very simple heuristic to detect useless asserts
        # better would be to use a parser and AST like tree-sitter
        useless_assert_list = [
            "Assert.IsEmpty(",
            "Assert.IsNotEmpty(",
            "Assert.IsNull(",
            "Assert.IsNotNull(",
        ]

        # search for "Assert." in source_code
        useless_asserts = 0
        all_asserts = 0
        for file in project.files:
            all_asserts += file.source_code.count("Assert.")
            for assert_ in useless_assert_list:
                useless_asserts += file.source_code.count(assert_)
        if all_asserts == 0:
            return 0
        perc_useless_asserts = useless_asserts / all_asserts * 100
        return round(100 - perc_useless_asserts, 2)
