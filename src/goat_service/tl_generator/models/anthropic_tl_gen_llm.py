import logging
import time

from gs_common.CodeProject import CodeProject
from langchain.chains.llm import LLMChain
from langchain.prompts.chat import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.outputs import LLMResult

from src.goat_service.tl_generator.models.tl_gen_llm import TLGenLLM, TLGenResult
from src.goat_service.tl_generator.prompts.tl_prompter import TLPrompter


class AnthropicTLGenLLM(TLGenLLM):
    def __init__(self, model, n_generations, temperature):
        self.model = model
        self.n_generations = n_generations
        self.temperature = temperature
        logging.info(f"Using model: {self.model}")
        self.llm = self.create_llm(self.n_generations)

    def create_llm(self, n_generations):
        return ChatAnthropic(
            model=self.model,
            # n=n_generations,
            temperature=self.temperature,
            timeout=60,
            max_retries=0,
        )

    def generate_translations(
        self, prompter: TLPrompter
    ) -> tuple[LLMResult, ChatPromptTemplate, str]:
        llm_result, prompt, question = self._generate_translations(prompter)

        tl_projects = prompter.process_llm_result(llm_result)
        return TLGenResult(
            tl_projects=tl_projects,
            llm_result=llm_result,
            prompt=prompt,
            question=question,
        )

    def _generate_translations(self, prompter: TLPrompter) -> TLGenResult:
        prompt = prompter.get_prompt()
        question = prompter.get_question()
        chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            return_final_only=False,
        )

        t0 = time.time()
        llm_result: LLMResult = chain.generate(
            input_list=[{"question": question}],
        )
        t_gen = time.time() - t0
        logging.info(f"Time to generate: {t_gen:.1f}s")

        return llm_result, prompt, question
