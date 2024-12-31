import logging
from copy import deepcopy
from abc import ABC

from gs_common.CodeProject import CodeProject
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.outputs.llm_result import LLMResult

from src.goat_service.utils.operation_applier import OperationApplier


class TLPrompter(ABC):
    system_message: str
    examples: list[str] = []

    def __init__(
        self,
        source_project: CodeProject,
        instruction: str = None,
        test_project: CodeProject = None,
    ):
        self.source_project = source_project
        self.instruction = instruction
        self.test_project = test_project
        self.additional_info = self.get_additional_info()

        # backup reference_files and log filenames
        self.source_project_reference_files = deepcopy(
            self.source_project.reference_files
        )
        self.source_project.reference_files = []
        logging.info(
            f"Source project filenames: {[f.file_name for f in source_project.files]}"
        )
        if self.test_project:
            self.test_project.reference_files = []
            logging.info(
                f"Test project filenames: {[f.file_name for f in test_project.files]}"
            )

    def get_additional_info(self) -> str:
        return None

    def get_prompt(self) -> ChatPromptTemplate:
        llm_prompt = HumanMessagePromptTemplate.from_template("{question}")
        return ChatPromptTemplate(
            messages=[
                self.system_message,
                *self.examples,
                llm_prompt,
            ],
            input_variables=["question"],
        )

    def get_question(self) -> str:
        q = ""
        if self.instruction:
            q += f"Instruction:\n{self.instruction}\n\n"
        if self.additional_info:
            q += f"Additional info:\n{self.additional_info}\n\n"
        q += str(self.source_project)
        if self.test_project:
            q += str(self.test_project)

        # limit to < 100k tokens ~ 400k chars
        char_limit = 300_000
        if len(q) > char_limit:
            logging.warning(
                f"Repo is too big ({len(q)} chars), truncating to {char_limit} chars"
            )
            q = q[:char_limit]

        return q

    def process_llm_result(self, response: LLMResult) -> list[CodeProject]:
        raw_generations = [generation.text for generation in response.generations[0]]
        parsed_projects = []
        bad_projects = []
        unique_generations = []

        for i, gen in enumerate(raw_generations):
            # NOTE: openai json mode is not available w langchain yet
            # sometimes llm generates json formatting around generation
            # remove in beginning and end
            if gen.startswith("```json\n"):
                gen = gen[8:]
            if gen.endswith("\n```"):
                gen = gen[:-4]

            # filter out duplicate generations
            gen_body = gen
            if "file_operations" in gen_body:
                gen_body = gen.split("file_operations")[1]

            if gen_body in unique_generations:
                logging.warning(f"Skipping duplicate generation {i}")
                continue
            unique_generations.append(gen_body)

            try:
                parsed, fully_successful = self.convert_to_code_project(gen)
                if not fully_successful:
                    bad_projects.append(parsed)
                else:
                    parsed_projects.append(parsed)
            except Exception as e:
                # if converting to json fails, skip it
                logging.error(f"Failed to convert generation {i} to CodeProject: {e}")
        n_fully_successful = len(parsed_projects)
        n_not_fully_successful = len(bad_projects)
        n_duplicates = len(raw_generations) - len(unique_generations)
        n_failed = (
            len(raw_generations)
            - n_fully_successful
            - n_not_fully_successful
            - n_duplicates
        )
        logging.info(
            f"Processed generations: {n_fully_successful=}, {n_not_fully_successful=}, {n_failed=}, {n_duplicates=}"
        )
        # add bad projects to the end
        parsed_projects.extend(bad_projects)
        return parsed_projects

    def convert_to_code_project(self, generation: str) -> tuple[CodeProject, bool]:
        da = OperationApplier(self.source_project, generation)
        new_project, success = da.apply()
        # add reference files
        new_project.reference_files = deepcopy(self.source_project_reference_files)
        return new_project, success
