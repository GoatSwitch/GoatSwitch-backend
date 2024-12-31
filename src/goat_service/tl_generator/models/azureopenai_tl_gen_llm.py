from langchain_openai import AzureChatOpenAI
from src.goat_service.tl_generator.models.openai_tl_gen_llm import OpenAITLGenLLM


class AzureOpenAITLGenLLM(OpenAITLGenLLM):
    def create_llm(self, n_generations):
        return AzureChatOpenAI(
            model=self.model,
            azure_deployment=self.model,
            # see https://learn.microsoft.com/en-us/azure/ai-services/openai/api-version-deprecation
            api_version="2024-02-01",
            azure_endpoint="https://gs-oai-sweden.openai.azure.com/",
            n=n_generations,
            temperature=self.temperature,
            request_timeout=60,
            max_retries=0,
        )
