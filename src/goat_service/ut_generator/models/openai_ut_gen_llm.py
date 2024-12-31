import logging
import time

from gs_common.CodeProject import CodeProject
from langchain.chains.llm import LLMChain
from langchain.prompts.chat import ChatPromptTemplate
from langchain_community.callbacks.manager import get_openai_callback
from langchain_core.outputs import LLMResult
from langchain_openai import ChatOpenAI

from src.goat_service.tl_generator.prompts.tl_prompter import TLPrompter
from src.goat_service.ut_generator.models.ut_gen_llm import UTGenLLM, UTGenResult


class OpenAIUTGenLLM(UTGenLLM):
    def __init__(self, model, n_generations, temperature):
        self.model = model
        self.n_generations = n_generations
        self.temperature = temperature
        logging.info(f"Using model: {self.model}")
        self.llm = self.create_llm(self.n_generations)

    def create_llm(self, n_generations):
        return ChatOpenAI(
            model=self.model,
            n=n_generations,
            temperature=self.temperature,
            request_timeout=60,
            max_retries=0,
        )

    def generate_unittests(
        self, prompter: TLPrompter
    ) -> tuple[LLMResult, ChatPromptTemplate, str]:
        llm_result, prompt, question = self._generate_unittests(prompter)

        ut_projects = prompter.process_llm_result(llm_result)
        return UTGenResult(
            ut_projects=ut_projects,
            llm_result=llm_result,
            prompt=prompt,
            question=question,
        )

    def _generate_unittests(self, prompter: TLPrompter) -> UTGenResult:
        prompt = prompter.get_prompt()
        question = prompter.get_question()
        chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            return_final_only=False,
        )

        with get_openai_callback() as cb:
            t0 = time.time()
            logging.info("I am calling the UT LLM now...")
            llm_result: LLMResult = chain.generate(
                input_list=[{"question": question}],
            )
            t_gen = time.time() - t0
            tps = cb.completion_tokens / t_gen / self.n_generations
            logging.info("OpenAICallback: %s", cb)
            logging.info(f"Tokens/s: {tps:.2f}")
            logging.info(f"Time to generate: {t_gen:.1f}s")

        return llm_result, prompt, question
