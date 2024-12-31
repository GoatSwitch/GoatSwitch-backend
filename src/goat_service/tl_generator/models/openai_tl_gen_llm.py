import asyncio
import logging
import time
from copy import deepcopy

from gs_common.CodeProject import CodeProject
from langchain.chains.llm import LLMChain
from langchain.prompts.chat import ChatPromptTemplate
from langchain_community.callbacks.manager import get_openai_callback
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import Generation, LLMResult
from langchain_openai import ChatOpenAI

from src.goat_service.tl_generator.models.tl_gen_llm import TLGenLLM, TLGenResult
from src.goat_service.tl_generator.prompts.tl_prompter import (
    TLPrompter,
)


class OpenAITLGenLLM(TLGenLLM):
    def __init__(self, model, n_generations, temperature):
        self.model = model
        self.n_generations = n_generations
        self.temperature = temperature
        logging.info(f"Using model: {self.model}")
        self.llm = self.create_llm(self.n_generations)
        # NOTE: make a new llm for async continuation to not have conflicts
        # NOTE: set n=1 to make single continuation generations
        self.llm_cont = self.create_llm(1)

    def create_llm(self, n_generations):
        return ChatOpenAI(
            model=self.model,
            n=n_generations,
            temperature=self.temperature,
            request_timeout=60,
            max_retries=0,
        )

    def generate_translations(self, prompter: TLPrompter) -> TLGenResult:
        llm_result, prompt, question = asyncio.run(
            self._generate_translations(prompter)
        )

        tl_projects = prompter.process_llm_result(llm_result)
        return TLGenResult(
            tl_projects=tl_projects,
            llm_result=llm_result,
            prompt=prompt,
            question=question,
        )

    async def _generate_translations(
        self, prompter: TLPrompter
    ) -> tuple[LLMResult, ChatPromptTemplate, str]:
        prompt: ChatPromptTemplate = prompter.get_prompt()
        question = prompter.get_question()
        chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            return_final_only=False,
        )
        with get_openai_callback() as cb:
            t0 = time.time()
            logging.info("I am calling the TL LLM now...")
            llm_result: LLMResult = chain.generate(input_list=[{"question": question}])
            logging.info(
                f"len(llm_result.generations): {len(llm_result.generations[0])}"
            )

            # check if all generations are completed successfully
            cont_tasks = []
            cont_idx = []
            for i, gen in enumerate(llm_result.generations[0]):
                finish_reason = gen.generation_info.get("finish_reason")
                if finish_reason != "stop":
                    logging.warning(
                        f"finish_reason for generation {i}: {finish_reason}"
                    )
                    logging.warning("Generation not completed, trying to continue")
                    task = generate_continuation(
                        gen,
                        self.llm_cont,
                        deepcopy(prompt),
                        deepcopy(question),
                    )
                    cont_tasks.append(task)
                    cont_idx.append(i)

            if cont_tasks:
                cont_results: list[Generation] = await asyncio.gather(
                    *cont_tasks, return_exceptions=True
                )
                # overwrite llm_result with new generations
                for i, new_gen in zip(cont_idx, cont_results):
                    if isinstance(new_gen, Exception):
                        logging.error(f"Error in cont generation {i}: {new_gen}")
                        continue
                    llm_result.generations[0][i] = new_gen

            t_gen = time.time() - t0
            tps = cb.completion_tokens / t_gen / self.n_generations
            logging.info("OpenAICallback: %s", cb)
            logging.info(f"Tokens/s: {tps:.2f}")
            logging.info(f"Time to generate: {t_gen:.1f}s")

        return llm_result, prompt, question


async def generate_continuation(
    last_gen: Generation, llm: ChatOpenAI, prompt: ChatPromptTemplate, question: str
) -> Generation:
    # cut off last message until last "file_name"
    cut_off_string = '"file_name":'
    clean_last_text = last_gen.text
    last_file_name = clean_last_text.rfind(cut_off_string)
    if last_file_name == -1:
        logging.error(
            "generate_continuation failed: cut_off_string not found; skipping"
        )
        return last_gen

    clean_last_text = clean_last_text[:last_file_name]
    logging.info(f"cut off generation last tokens:\n{clean_last_text[-50:]}")

    prompt.messages.append(AIMessage(content=clean_last_text))
    cont_msg = """\
        The last message was cut off at {cut_off_string}
        Please continue exactly where you left off. 
        Do not start from the beginning. 
        Start with {cut_off_string} again The messages will be merged later.
        """.format(cut_off_string=cut_off_string)
    prompt.messages.append(HumanMessage(content=cont_msg))
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        return_final_only=False,
    )

    new_llm_result: LLMResult = await chain.agenerate(
        input_list=[{"question": question}],
    )

    new_gen = new_llm_result.generations[0][0]
    logging.info(f"new generation first tokens:\n{new_gen.text[:50]}")
    logging.info(f"new generation last tokens:\n{new_gen.text[-50:]}")

    finish_reason = new_llm_result.generations[0][0].generation_info.get(
        "finish_reason"
    )
    if finish_reason != "stop":
        logging.error(
            "Generation still not completed; Current continue implementation works only for 1 continuation; Skipping"
        )
        return new_gen

    # Merge
    new_text = new_gen.text.replace("```json", "")
    # handle edge case last { token repeated
    clean_last_text = clean_last_text.strip()
    new_text = new_text.strip()
    logging.info(f"last 10 chars last_gen:>{clean_last_text[-10:]}<")
    logging.info(f"first 10 chars new_gen:>{new_text[:10]}<")
    if clean_last_text[-1] == "{" and new_text[0] == "{":
        clean_last_text = clean_last_text[:-1]

    new_gen.text = clean_last_text + new_text
    return new_gen
