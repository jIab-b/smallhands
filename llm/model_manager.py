"""
LLM model manager for SmallHands.
"""
from .openai_model import OpenAIModel

class ModelManager:
    """A simple wrapper for a single language model."""
    def __init__(self, model: OpenAIModel):
        self.model = model

    def generate(self, prompt: str) -> str:
        """Generates a response from the model."""
        return self.model.complete(prompt)
