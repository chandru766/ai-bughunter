import os
from .base import LLMProvider
import openai

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.model = os.getenv("LLM_MODEL", "gpt-4-turbo")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        
        # Architectural enforcement: Never log the key
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key, timeout=self.timeout)
        else:
            self.client = None
            
    def analyze(self, prompt: str) -> str:
        if not self.client:
            raise ValueError("LLM_API_KEY not configured")
        
        response = self.client.chat.completions.create(
            model=self.model,
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "You are a Bug Bounty AI Assistant. Always output JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
