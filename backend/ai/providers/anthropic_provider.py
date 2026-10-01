import os
from .base import LLMProvider
import anthropic

class AnthropicProvider(LLMProvider):
    def __init__(self):
        self.model = os.getenv("LLM_MODEL", "claude-3-opus-20240229")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key, timeout=self.timeout)
        else:
            self.client = None
            
    def analyze(self, prompt: str) -> str:
        if not self.client:
            raise ValueError("LLM_API_KEY not configured")
            
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system="You are a Bug Bounty AI Assistant. Always output JSON.",
            messages=[
                {"role": "user", "content": prompt + "\n\nPlease respond with valid JSON only."}
            ]
        )
        return response.content[0].text
