from gs_common.CodeProject import CodeProject, CodeFile
from typing import Dict
from rapidfuzz import process, fuzz
import logging


class TLPostProcessor:
    def __init__(self, source_project: CodeProject) -> None:
        self.source_project = source_project

    def post_process(self, code_project: CodeProject) -> CodeProject:
        # Make sure solutions have the same display_name as the source project
        code_project.display_name = self.source_project.display_name
        # Rename the files in the translated project to match the source project
        name_map = self.fuzzy_match_file_names(
            self.source_project.files, code_project.files
        )
        code_project = self.rename_files(code_project, name_map)
        return code_project

    def rename_files(
        self, code_project: CodeProject, name_map: Dict[str, str]
    ) -> CodeProject:
        for file in code_project.files:
            if file.file_name in name_map:
                file.file_name = name_map[file.file_name]
        return code_project

    def fuzzy_match_file_names(
        self, source_files: list[CodeFile], trans_files: list[CodeFile]
    ) -> Dict[str, str]:
        """
        Match the file names of the source project to the translated project
        Returns a dictionary indicating renaming of the translated files
        Might not contain renaming for all files or none at all
        :param source_files: list of source project files
        :param trans_files: list of translated project files
        :return: dictionary indicating renaming of the translated files
        """
        name_map = {}
        source_content = [f.source_code for f in source_files]
        for t_file in trans_files:
            match_tuple = process.extractOne(
                t_file.source_code, source_content, scorer=fuzz.WRatio, score_cutoff=60
            )
            if match_tuple:
                match, score, idx = match_tuple
                # filter matches where file endings differ
                ending_source = source_files[idx].file_name.split(".")[-1]
                ending_trans = t_file.file_name.split(".")[-1]
                if ending_source == ending_trans:
                    name_map[t_file.file_name] = source_files[idx].file_name
                    logging.debug(
                        f"Matched {t_file.file_name} to {source_files[idx].file_name} with score {score}"
                    )
        # remove duplicate values by reversing the dictionary
        # and then reversing it back, keys are unique
        name_map = {v: k for k, v in name_map.items()}
        name_map = {v: k for k, v in name_map.items()}
        return name_map

    def post_process_all(self, code_projects: list[CodeProject]) -> list[CodeProject]:
        post_processed_projects: list[CodeProject] = []
        for project in code_projects:
            post_processed_projects.append(self.post_process(project))
        return post_processed_projects
