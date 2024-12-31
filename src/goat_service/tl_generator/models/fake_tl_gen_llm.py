import json
import logging

from gs_common.CodeProject import CodeProject
from langchain_core.outputs import Generation, LLMResult

from src.goat_service.tl_generator.models.tl_gen_llm import TLGenLLM, TLGenResult
from src.goat_service.tl_generator.prompts.tl_prompter import (
    TLPrompter,
)


class FakeTLGenLLM(TLGenLLM):
    def __init__(self, debug_file):
        # load debug file as json
        logging.info(f"Loading debug file {debug_file}")
        with open(debug_file, "r") as f:
            debug_llm_output = json.load(f)
        # load llm_result from nested json
        debug_llm_result = json.loads(debug_llm_output["llm_result"])
        # convert it to LLMResult
        gens = [
            Generation(text=gen["text"]) for gen in debug_llm_result["generations"][0]
        ]
        logging.info(f"Loaded {len(gens)} generations from debug file")
        self.debug_llm_result = LLMResult(generations=[gens])

        # could also be parsed
        self.prompt = None
        self.question = None

    def generate_translations(self, prompter: TLPrompter) -> TLGenResult:
        return prompter.process_llm_result(self.debug_llm_result)
