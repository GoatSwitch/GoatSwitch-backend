import logging

import gs_common.proto.ut_generator_pb2 as uts_proto
import yaml
from dapr.ext.grpc import InvokeMethodRequest
from google.protobuf.json_format import MessageToDict
from gs_common.CodeProject import CodeFile, CodeProject
from gs_common.file_ops import (
    backup_dict_in_background,
    generate_save_dir,
)
from gs_common.proto.common_pb2 import CodeProject as ProtoCodeProject
from gs_common.tracing import extract_trace_info

from dataset.util import load_example_project
from src.goat_service.ut_generator.models.anthropic_ut_gen_llm import AnthropicUTGenLLM
from src.goat_service.ut_generator.models.azureopenai_ut_gen_llm import (
    AzureOpenAIUTGenLLM,
)
from src.goat_service.ut_generator.models.fake_ut_gen_llm import FakeUTGenLLM
from src.goat_service.ut_generator.models.openai_ut_gen_llm import OpenAIUTGenLLM
from src.goat_service.ut_generator.models.ut_gen_llm import UTGenLLM, UTGenResult
from src.goat_service.ut_generator.prompts.junit_ut_improve_prompter import (
    JUnitUTImprovePrompter,
)
from src.goat_service.ut_generator.prompts.junit_ut_prompter import (
    JUnitUnitTestPrompter,
)
from src.goat_service.ut_generator.prompts.nunit_improve_ut_prompter import (
    NUnitImproveUTPrompter,
)
from src.goat_service.ut_generator.prompts.nunit_ut_prompter import (
    NUnitUTPrompter,
)
from src.goat_service.ut_generator.prompts.universal_ut_prompter import (
    UniversalUTPrompter,
)
from src.goat_service.ut_generator.utils.ut_postprocessor import (
    UnitTestPostProcessor,
)


class UTGenService:
    def __init__(self):
        with open("config.yaml", "r") as f:
            self.config = yaml.safe_load(f)
        self.backup_base_dir = self.config["backup_base_dir"]
        self.use_nunit_dummy_test_project = self.config[
            "mode_ut_gen_use_nunit_dummy_test_project"
        ]
        self.ut_gen_llm: UTGenLLM = self.initialize_ut_gen_llm(
            self.config["ut_model"],
            self.config["n_ut_generations"],
            self.config["ut_temperature"],
            self.config["ut_gen_debug_output"],
        )
        self.backup_ut_gen_llm: UTGenLLM = self.initialize_ut_gen_llm(
            self.config["backup_model"],
            self.config["n_ut_generations"],
            self.config["ut_temperature"],
            self.config["ut_gen_debug_output"],
        )
        self.gslite_ut_gen_llm: UTGenLLM = self.initialize_ut_gen_llm(
            self.config["gslite_ut_model"],
            self.config["n_gslite_ut_generations"],
            self.config["gslite_ut_temperature"],
            self.config["gslite_ut_gen_debug_output"],
        )
        self.backup_gslite_ut_gen_llm: UTGenLLM = self.initialize_ut_gen_llm(
            self.config["backup_model"],
            self.config["n_gslite_ut_generations"],
            self.config["gslite_ut_temperature"],
            self.config["gslite_ut_gen_debug_output"],
        )

    def initialize_ut_gen_llm(
        self,
        model: str,
        n_generations: int,
        temperature: float,
        debug_output: bool,
    ) -> UTGenLLM:
        if debug_output:
            return FakeUTGenLLM(debug_output)
        elif "GS-" in model:
            return AzureOpenAIUTGenLLM(model, n_generations, temperature)
        elif "gpt" in model or model.startswith("o1"):
            return OpenAIUTGenLLM(model, n_generations, temperature)
        elif "claude" in model:
            return AnthropicUTGenLLM(model, n_generations, temperature)
        else:
            raise Exception(f"Unsupported model: {model}")

    def generate_unittests(
        self,
        request: InvokeMethodRequest,
    ) -> uts_proto.UTGeneratorResponse:
        extract_trace_info(request)
        req_proto = uts_proto.UTGeneratorRequest()
        req_proto = req_proto.FromString(request.proto.value)
        source_project = CodeProject.model_validate(
            MessageToDict(req_proto.source_project)
        )
        post_processor = UnitTestPostProcessor(source_project)

        target_language = req_proto.target_language
        logging.info(f"Target language: {target_language}")

        instruction = req_proto.instruction
        # log in one line
        logging.info("Instruction: " + instruction.replace("\n", " "))

        test_project = CodeProject.model_validate(MessageToDict(req_proto.test_project))

        if target_language == "dotnet8" and self.use_nunit_dummy_test_project:
            dummy_project = load_example_project("Dummy-GSTests", "nunit_unittests")
            post_processor.load_dotnet_csproj()
            dummy_project = post_processor.post_process_all([dummy_project])[0]
            return uts_proto.UTGeneratorResponse(
                solutions=[ProtoCodeProject(**dummy_project.model_dump())],
                return_code=uts_proto.SUCCESS,
            )

        if target_language == "gslite":
            prompter = UniversalUTPrompter(source_project, instruction, test_project)

        elif target_language == "dotnet8":
            post_processor.load_dotnet_csproj()
            if instruction == "":
                prompter = NUnitUTPrompter(source_project)
            elif test_project is None or len(test_project.files) == 0:
                prompter = NUnitUTPrompter(source_project, instruction)
            else:
                prompter = NUnitImproveUTPrompter(
                    source_project, instruction, test_project
                )
        elif target_language == "java21":
            if instruction == "":
                prompter = JUnitUnitTestPrompter(source_project)
            elif instruction != "" and (
                test_project is None or len(test_project.files) == 0
            ):
                prompter = JUnitUTImprovePrompter(source_project, instruction)
            else:
                logging.error("Unsupported java prompt: instruction + test_project")
                return uts_proto.UTGeneratorResponse(
                    error="Unsupported java prompt: instruction + test_project",
                    return_code=uts_proto.ERROR,
                )
        else:
            logging.error(f"Unsupported target language: {target_language}")
            return uts_proto.UTGeneratorResponse(
                error=f"Unsupported target language: {target_language}",
                return_code=uts_proto.ERROR,
            )

        try:
            try:
                if target_language == "gslite":
                    ut_gen_result: UTGenResult = (
                        self.gslite_ut_gen_llm.generate_unittests(prompter)
                    )
                else:
                    ut_gen_result: UTGenResult = self.ut_gen_llm.generate_unittests(
                        prompter
                    )
            except Exception as e:
                logging.error(f"Error generating unittests: {e}")
                logging.info("Retrying with backup model")
                if target_language == "gslite":
                    ut_gen_result: UTGenResult = (
                        self.backup_gslite_ut_gen_llm.generate_unittests(prompter)
                    )
                else:
                    ut_gen_result: UTGenResult = (
                        self.backup_ut_gen_llm.generate_unittests(prompter)
                    )

            if len(ut_gen_result.ut_projects) == 0:
                logging.error("No unittest generations found.")
                return uts_proto.UTGeneratorResponse(
                    error="No unittest generations found.", return_code=uts_proto.ERROR
                )
            logging.info(
                f"Generated {len(ut_gen_result.ut_projects)} unittest generations."
            )
            ut_projects = post_processor.post_process_all(ut_gen_result.ut_projects)
            return uts_proto.UTGeneratorResponse(
                solutions=[ProtoCodeProject(**x.model_dump()) for x in ut_projects],
                return_code=uts_proto.SUCCESS,
            )
        except Exception as e:
            msg = f"Error generating unittests: {e}"
            logging.error(msg)
            return uts_proto.UTGeneratorResponse(
                error=msg, return_code=uts_proto.FAILED
            )
        finally:
            try:
                save_dir = generate_save_dir("ut-gen")
                backup_dict_in_background(
                    {
                        "prompt": ut_gen_result.prompt.model_dump_json(),
                        "question": ut_gen_result.question,
                        "llm_result": ut_gen_result.llm_result.model_dump_json(),
                    },
                    backup_base_dir=self.backup_base_dir,
                    save_dir=save_dir,
                )
            except Exception as e:
                logging.error(f"Error saving backup: {e}")
