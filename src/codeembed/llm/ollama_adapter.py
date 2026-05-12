from typing import List, Type, TypeVar

import ollama
from pydantic import BaseModel

from codeembed.llm.base import LLMServiceBase
from codeembed.llm.models import ChatMessage

T = TypeVar("T", bound=BaseModel)


class OllamaLLMService(LLMServiceBase):
    # TODO: Consider making it possible to specify Ollama host and port.

    def generate_structured_output(self, messages: List[ChatMessage], llm_model: str, output_format: Type[T]) -> T:

        resp = ollama.chat(
            model=llm_model,
            messages=messages,
            format="json",
        )

        data = resp["message"]["content"]

        return output_format.model_validate_json(data)

    def generate_response(self, messages: List[ChatMessage], llm_model: str) -> str:

        resp = ollama.chat(
            model=llm_model,
            messages=messages,
        )

        content = resp["message"]["content"]

        return content
