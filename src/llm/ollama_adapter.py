"""Ollama adapter."""

from typing import Dict, List, Type, TypeVar

import ollama
from pydantic import BaseModel

from src.llm.base import LLMServiceBase

T = TypeVar("T", bound=BaseModel)


class OllamaLLMService(LLMServiceBase):
    def generate_structured_output(
        self, messages: List[Dict[str, str]], llm_model: str, output_format: Type[T]
    ) -> T:

        resp = ollama.chat(
            model=llm_model,
            messages=messages,
            format="json",
        )

        data = resp["message"]["content"]

        return output_format.model_validate_json(data)

    def generate_response(self, messages: List[Dict[str, str]], llm_model: str) -> str:
        """Uses ollama to generate a response."""

        resp = ollama.chat(
            model=llm_model,
            messages=messages,
        )

        content = resp["message"]["content"]

        return content
