from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def analyze(self, prompt: str) -> str:
        """
        Sends the constructed prompt to the LLM and returns raw text.
        """
        pass
