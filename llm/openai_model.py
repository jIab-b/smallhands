"""OpenAI model wrapper."""

import os
import openai
from typing import Dict, Any

class OpenAIModel:
    def __init__(self, model_name: str):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = model_name

    def complete(self, prompt: str, context: Dict[str, Any] = None) -> str:
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        if context:
            messages.append({"role": "assistant", "content": str(context)})
        messages.append({"role": "user", "content": prompt})
        response = openai.ChatCompletion.create(model=self.model_name, messages=messages)
        return response.choices[0].message.content
