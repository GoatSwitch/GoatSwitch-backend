from abc import ABC, abstractmethod
from dataclasses import dataclass

from langchain_core.outputs import LLMResult
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from src.goat_service.tl_generator.prompts.tl_prompter import TLPrompter


@dataclass
class UTGenResult:
    ut_projects: list[BaseModel]
    llm_result: LLMResult
    prompt: ChatPromptTemplate
    question: str


class UTGenLLM(ABC):
    @abstractmethod
    def __init__(self, model, n_generations, temperature):
        pass

    @abstractmethod
    def generate_unittests(self, prompter: TLPrompter) -> UTGenResult:
        pass
