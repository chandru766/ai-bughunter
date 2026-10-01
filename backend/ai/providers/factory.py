import os
from .mock_provider import MockProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider

class ProviderFactory:
    @staticmethod
    def get_provider():
        """
        Dynamically select the AI provider based on environment variables.
        Defaults to MockProvider for safe local testing.
        """
        provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
        if provider_name == "openai":
            return OpenAIProvider()
        elif provider_name == "anthropic":
            return AnthropicProvider()
        
        return MockProvider()
