import asyncio
import logging
import xml.etree.ElementTree as ET

import yaml
from dapr.ext.grpc import InvokeMethodRequest
from google.protobuf.json_format import MessageToDict
from gs_common.CodeProject import CodeProject
from gs_common.file_ops import (
    backup_dict_in_background,
    generate_save_dir,
)
from gs_common.proto.common_pb2 import CodeProject as ProtoCodeProject
from gs_common.proto.tl_generator_pb2 import (
    PlanGeneratorResponse,
    ReturnCode,
    TLGeneratorRequest,
    TLGeneratorResponse,
)
from gs_common.tracing import current_company_id, current_trace_id, extract_trace_info
from langchain_core.tracers.context import tracing_v2_enabled

from src.goat_service.tl_generator.models.anthropic_tl_gen_llm import AnthropicTLGenLLM
from src.goat_service.tl_generator.models.azureopenai_tl_gen_llm import (
    AzureOpenAITLGenLLM,
)
from src.goat_service.tl_generator.models.fake_tl_gen_llm import FakeTLGenLLM
from src.goat_service.tl_generator.models.openai_tl_gen_llm import OpenAITLGenLLM
from src.goat_service.tl_generator.models.tl_gen_llm import TLGenLLM, TLGenResult
from src.goat_service.tl_generator.prompts.aspnet_plan_prompter import (
    AspNetPlanPrompter,
)
from src.goat_service.tl_generator.prompts.dotnet8_improve_tl_prompter import (
    DotNet8ImproveTLPrompter,
)
from src.goat_service.tl_generator.prompts.java8_java21_tl_prompter import (
    Java8ToJava21TLPrompter,
)
from src.goat_service.tl_generator.prompts.java21_improve_prompter import (
    Java21ImprovePrompter,
)
from src.goat_service.tl_generator.prompts.universal_plan_prompter import (
    AIPlan,
    UniversalPlanPrompter,
)
from src.goat_service.tl_generator.prompts.universal_tl_prompter import (
    UniversalTLPrompter,
)
from src.goat_service.utils.grpc_code_executor_calls import (
    _call_pre_migration_assessor,
    _call_upgrade_assistant,
)


class TLGenService:
    def __init__(self):
        with open("config.yaml", "r") as f:
            self.config = yaml.safe_load(f)
        self.backup_base_dir = self.config["backup_base_dir"]
        self.tl_gen_llm: TLGenLLM = self.initialize_tl_gen_llm(
            self.config["tl_model"],
            self.config["n_tl_generations"],
            self.config["tl_temperature"],
            self.config["tl_gen_debug_output"],
        )
        self.backup_tl_gen_llm: TLGenLLM = self.initialize_tl_gen_llm(
            self.config["backup_model"],
            self.config["n_tl_generations"],
            self.config["tl_temperature"],
            self.config["tl_gen_debug_output"],
        )
        self.gslite_tl_gen_llm: TLGenLLM = self.initialize_tl_gen_llm(
            self.config["gslite_tl_model"],
            self.config["n_gslite_tl_generations"],
            self.config["gslite_tl_temperature"],
            self.config["gslite_tl_gen_debug_output"],
        )
        self.backup_gslite_tl_gen_llm: TLGenLLM = self.initialize_tl_gen_llm(
            self.config["backup_model"],
            self.config["n_gslite_tl_generations"],
            self.config["gslite_tl_temperature"],
            self.config["gslite_tl_gen_debug_output"],
        )

    def initialize_tl_gen_llm(
        self,
        model: str,
        n_generations: int,
        temperature: float,
        debug_output: bool,
    ) -> TLGenLLM:
        if debug_output:
            return FakeTLGenLLM(debug_output)
        elif "GS-" in model:
            return AzureOpenAITLGenLLM(model, n_generations, temperature)
        elif "gpt" in model or model.startswith("o1"):
            return OpenAITLGenLLM(model, n_generations, temperature)
        elif "claude" in model:
            return AnthropicTLGenLLM(model, n_generations, temperature)
        else:
            raise Exception(f"Unsupported model: {model}")

    def assess(self, request: InvokeMethodRequest) -> TLGeneratorResponse:
        source_project, target_language, _, _ = self.parse_tl_request(request)

        if target_language != "dotnet8":
            return TLGeneratorResponse(
                error=f"Unsupported target language: {target_language}",
                return_code=ReturnCode.ERROR,
            )

        try:
            response = asyncio.run(
                _call_pre_migration_assessor(source_project, target_language)
            )
            if "error" in response:
                return TLGeneratorResponse(
                    error=response["error"], return_code=ReturnCode.ERROR
                )
            if "assessment_result" not in response:
                return TLGeneratorResponse(
                    error="No assessment_result and no error in response",
                    return_code=ReturnCode.ERROR,
                )
            assessment_result = CodeProject.model_validate(
                response["assessment_result"]
            )
            return TLGeneratorResponse(
                solutions=[ProtoCodeProject(**assessment_result.model_dump())],
                return_code=ReturnCode.SUCCESS,
            )
        except Exception as e:
            return TLGeneratorResponse(error=str(e), return_code=ReturnCode.ERROR)

    def generate_translations(
        self,
        request: InvokeMethodRequest,
    ) -> TLGeneratorResponse:
        source_project, target_language, instruction, model = self.parse_tl_request(
            request
        )

        if model == "UPGRADE_DOTNET_PROJECT":
            return self.start_upgrade_assistant_request(source_project, target_language)
        if model == "RESTRUCTURE_PROJECT_FROM_ASPNET_TO_ASPNETCORE":
            return self.start_restructure_project_request(
                source_project, target_language
            )
        if model == "RENAME_VARIABLE":
            return self.start_rename_variable_request(
                source_project, target_language, instruction
            )
        if model == "RENAME_VARIABLE_GLOBAL":
            return self.start_rename_variable_global_request(
                source_project, target_language, instruction
            )

        # NOTE: disabled for now
        if current_company_id.get() != "-1":
            return self.start_tl_gen_request(
                source_project,
                target_language,
                model,
                instruction,
            )

        with tracing_v2_enabled(
            tags=[source_project.display_name, current_trace_id.get()]
        ):
            return self.start_tl_gen_request(
                source_project,
                target_language,
                model,
                instruction,
            )

    def generate_plan(
        self,
        request: InvokeMethodRequest,
    ) -> PlanGeneratorResponse:
        source_project, _, instruction, _ = self.parse_tl_request(request)

        tl_gen_result: TLGenResult = None
        try:
            if self._is_aspnet_project(source_project):
                prompter = AspNetPlanPrompter(source_project, instruction)
            else:
                prompter = UniversalPlanPrompter(source_project, instruction)

            try:
                tl_gen_result: TLGenResult = (
                    self.gslite_tl_gen_llm.generate_translations(prompter)
                )
            except Exception as e:
                logging.error(f"Error generating plan: {e}")
                logging.info("Retrying with backup model")
                tl_gen_result: TLGenResult = (
                    self.backup_gslite_tl_gen_llm.generate_translations(prompter)
                )
            logging.info(
                f"Finished with {len(tl_gen_result.tl_projects )} tl_projects "
            )
            if not tl_gen_result.tl_projects:
                return TLGeneratorResponse(
                    error="No plan generated", return_code=ReturnCode.ERROR
                )

            # NOTE: right now we only have one generation for planning model
            ai_plan: AIPlan = tl_gen_result.tl_projects[0]
            # log in one line
            logging.info(f"Generated plan: {ai_plan.model_dump_json()}")

            return PlanGeneratorResponse(
                plan=ai_plan.model_dump(),
                return_code=ReturnCode.SUCCESS,
            )

        except Exception as e:
            msg = f"Error generating plan: {e}"
            logging.error(msg)
            return PlanGeneratorResponse(
                plan={}, error=msg, return_code=ReturnCode.ERROR
            )
        finally:
            if not tl_gen_result or not tl_gen_result.tl_projects:
                logging.error("No plan generated")
            else:
                self.backup(tl_gen_result)

    def _is_aspnet_project(self, source_project: CodeProject) -> bool:
        # search for csproj
        for file in source_project.files:
            if file.file_name.endswith(".csproj"):
                # check if "System.Web" is in the csproj file
                if "System.Web" in file.source_code:
                    return True
        return False

    def start_tl_gen_request(
        self,
        source_project: CodeProject,
        target_language: str,
        model: str,
        instruction: str,
    ) -> TLGeneratorResponse:
        tl_gen_result: TLGenResult = None
        try:
            if target_language == "gslite":
                prompter = UniversalTLPrompter(source_project, instruction)

            elif target_language == "dotnet8":
                if instruction == "":
                    return TLGeneratorResponse(
                        error="Instruction is required for dotnet8 improvement",
                        return_code=ReturnCode.ERROR,
                    )
                prompter = DotNet8ImproveTLPrompter(source_project, instruction)

            elif target_language == "java21":
                if instruction == "":
                    prompter = Java8ToJava21TLPrompter(source_project)
                else:
                    prompter = Java21ImprovePrompter(source_project, instruction)

            else:
                return TLGeneratorResponse(
                    error=f"Unsupported target language: {target_language}",
                    return_code=ReturnCode.ERROR,
                )

            try:
                if target_language == "gslite":
                    tl_gen_result: TLGenResult = (
                        self.gslite_tl_gen_llm.generate_translations(prompter)
                    )
                else:
                    tl_gen_result: TLGenResult = self.tl_gen_llm.generate_translations(
                        prompter
                    )
            except Exception as e:
                logging.error(f"Error generating translations: {e}")
                logging.info("Retrying with backup model")
                if target_language == "gslite":
                    tl_gen_result = self.backup_gslite_tl_gen_llm.generate_translations(
                        prompter
                    )
                else:
                    tl_gen_result = self.backup_tl_gen_llm.generate_translations(
                        prompter
                    )

            logging.info(
                f"Finished with {len(tl_gen_result.tl_projects )} tl_projects "
            )
            if not tl_gen_result.tl_projects:
                return TLGeneratorResponse(
                    error="No generated translations", return_code=ReturnCode.ERROR
                )
            return TLGeneratorResponse(
                solutions=[
                    ProtoCodeProject(**x.model_dump())
                    for x in tl_gen_result.tl_projects
                ],
                return_code=ReturnCode.SUCCESS,
            )

        except Exception as e:
            msg = f"Error generating translations: {e}"
            logging.error(msg)
            return TLGeneratorResponse(
                solutions=[], error=msg, return_code=ReturnCode.ERROR
            )
        finally:
            if not tl_gen_result or not tl_gen_result.tl_projects:
                logging.error("No tl_projects generated")
            else:
                self.backup(tl_gen_result)

    def parse_tl_request(self, request: InvokeMethodRequest):
        extract_trace_info(request)
        req_proto = TLGeneratorRequest()
        request.unpack(req_proto)
        source_project = CodeProject.model_validate(
            MessageToDict(req_proto.source_project)
        )
        target_language = req_proto.target_language
        logging.info(f"Target language: {target_language}")
        instruction = req_proto.instruction
        # log in one line
        logging.info("Instruction:" + instruction.replace("\n", " "))
        model = req_proto.model
        logging.info(f"Model: {model}")
        return source_project, target_language, instruction, model

    def backup(
        self,
        tl_gen_result: TLGenResult,
    ):
        try:
            save_dir = generate_save_dir("tl-gen")
            backup_dict_in_background(
                {
                    "prompt": tl_gen_result.prompt.model_dump_json(),
                    "question": tl_gen_result.question,
                    "llm_result": tl_gen_result.llm_result.model_dump_json(),
                },
                backup_base_dir=self.backup_base_dir,
                save_dir=save_dir,
            )
        except Exception as e:
            logging.error(f"Error saving backup: {e}")

    def start_upgrade_assistant_request(
        self,
        source_project: CodeProject,
        target_language: str,
    ) -> TLGeneratorResponse:
        try:
            response = asyncio.run(
                _call_upgrade_assistant(source_project, target_language)
            )
            if "error" in response:
                return TLGeneratorResponse(
                    error=response["error"], return_code=ReturnCode.ERROR
                )
            if "upgraded_project" not in response:
                return TLGeneratorResponse(
                    error="No upgraded_project and no error in response",
                    return_code=ReturnCode.ERROR,
                )
            upgraded_project = CodeProject.model_validate(response["upgraded_project"])
            return TLGeneratorResponse(
                solutions=[ProtoCodeProject(**upgraded_project.model_dump())],
                return_code=ReturnCode.SUCCESS,
            )
        except Exception as e:
            return TLGeneratorResponse(error=str(e), return_code=ReturnCode.ERROR)

    def start_restructure_project_request(
        self,
        source_project: CodeProject,
        target_language: str,
    ) -> TLGeneratorResponse:
        try:
            # call
            upgraded_project = self._call_restructure_project(
                source_project, target_language
            )

            return TLGeneratorResponse(
                solutions=[ProtoCodeProject(**upgraded_project.model_dump())],
                return_code=ReturnCode.SUCCESS,
            )
        except Exception as e:
            return TLGeneratorResponse(error=str(e), return_code=ReturnCode.ERROR)

    def _call_restructure_project(
        self,
        source_project: CodeProject,
        target_language: str,
    ) -> CodeProject:
        """
        Restructure the project from ASP.NET to ASP.NET Core.
        remove all files in App_Start folder
        remove all files in Content folder
        remove all files in Scripts folder
        remove all web.config files and web.debug.config and web.release.config and Views/web.config
        """

        # remove all files in App_Start folder
        source_project.files = [
            x for x in source_project.files if "App_Start" not in x.file_name
        ]

        # remove all files in Content folder
        source_project.files = [
            x for x in source_project.files if "Content" not in x.file_name
        ]

        # remove all files in Scripts folder
        source_project.files = [
            x for x in source_project.files if "Scripts" not in x.file_name
        ]

        # remove all web.config files and web.debug.config and web.release.config and Views/web.config
        source_project.files = [
            x
            for x in source_project.files
            if "web.config" not in x.file_name.lower()
            and "web.debug.config" not in x.file_name.lower()
            and "web.release.config" not in x.file_name.lower()
        ]

        # create a empty wwwroot folder (trick: place a .gitkeep file in it)
        source_project.add_file(
            file_name="wwwroot/.gitkeep",
            source_code="",
        )

        # modify csproj file: remove everything from first ItemGroup to end
        for file in source_project.files:
            if file.file_name.endswith(".csproj"):
                file.source_code = file.source_code.split("<ItemGroup>")[0]
                # add end tag
                file.source_code += "</Project>"

        return source_project

    def start_rename_variable_request(
        self,
        source_project: CodeProject,
        target_language: str,
        instruction: str,
    ) -> TLGeneratorResponse:
        try:
            # call
            upgraded_project = self._call_rename_variable(
                source_project, target_language, instruction
            )

            return TLGeneratorResponse(
                solutions=[ProtoCodeProject(**upgraded_project.model_dump())],
                return_code=ReturnCode.SUCCESS,
            )
        except Exception as e:
            return TLGeneratorResponse(error=str(e), return_code=ReturnCode.ERROR)

    def _call_rename_variable(
        self,
        source_project: CodeProject,
        target_language: str,
        instruction: str,
    ) -> CodeProject:
        """
        Rename all occurrences of a string in a file.
        Usage: (xml like)
        Description: Use <rename_variable old_name="old_name" new_name="new_name" file_path="file_path" />
        """
        # parse description/instruction with xml parser
        # only parse current task
        instruction = instruction.split("# Current task:")[1]
        xml_part = (
            "<rename_variable"
            + instruction.split("<rename_variable")[1].split("/>")[0]
            + "/>"
        )
        root = ET.fromstring(xml_part)
        old_name = root.attrib["old_name"]
        new_name = root.attrib["new_name"]
        file_path = root.attrib["file_path"]

        # find file
        file = source_project.get_file(file_path)
        if file is None:
            raise Exception(f"File not found: {file_path}")

        # replace old_name with new_name
        if old_name not in file.source_code:
            raise Exception(
                f"rename_variable failed: {old_name} not found in file {file_path}"
            )

        file.source_code = file.source_code.replace(old_name, new_name)
        return source_project

    def start_rename_variable_global_request(
        self,
        source_project: CodeProject,
        target_language: str,
        instruction: str,
    ) -> TLGeneratorResponse:
        try:
            # call
            upgraded_project = self._call_rename_variable_global(
                source_project, target_language, instruction
            )

            return TLGeneratorResponse(
                solutions=[ProtoCodeProject(**upgraded_project.model_dump())],
                return_code=ReturnCode.SUCCESS,
            )
        except Exception as e:
            return TLGeneratorResponse(error=str(e), return_code=ReturnCode.ERROR)

    def _call_rename_variable_global(
        self,
        source_project: CodeProject,
        target_language: str,
        instruction: str,
    ) -> CodeProject:
        """
        Rename all occurrences of a string in all files.
        Usage: (xml like)
        Description: Use <rename_variable_global old_name="old_name" new_name="new_name" />
        """
        # parse description/instruction with xml parser
        # only parse current task
        instruction = instruction.split("# Current task:")[1]
        xml_part = (
            "<rename_variable_global"
            + instruction.split("<rename_variable_global")[1].split("/>")[0]
            + "/>"
        )
        root = ET.fromstring(xml_part)
        old_name = root.attrib["old_name"]
        new_name = root.attrib["new_name"]

        # replace all occurrences of old_name with new_name
        for file in source_project.files:
            file.source_code = file.source_code.replace(old_name, new_name)
        return source_project
