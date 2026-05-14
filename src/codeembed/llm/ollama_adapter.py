from typing import List, Optional, Type, TypeVar

import ollama
from pydantic import BaseModel

from codeembed.llm.base import LLMServiceBase
from codeembed.llm.models import ChatMessage, LLMResponse, StructuredLLMResponse

T = TypeVar("T", bound=BaseModel)


class OllamaLLMService(LLMServiceBase):
    def generate_structured_output(
        self,
        messages: List[ChatMessage],
        llm_model: str,
        output_format: Type[T],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> StructuredLLMResponse[T]:

        options = {}
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if temperature is not None:
            options["temperature"] = temperature

        resp = ollama.chat(model=llm_model, messages=messages, format="json", options=options)

        data = resp["message"]["content"]

        model = output_format.model_validate_json(data)

        return StructuredLLMResponse(
            input_tokens=resp["prompt_eval_count"] or 0,
            output_tokens=resp["eval_count"] or 0,
            data=model,
            llm_model=llm_model,
        )

    def generate_response(
        self,
        messages: List[ChatMessage],
        llm_model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:

        options = {}
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if temperature is not None:
            options["temperature"] = temperature

        resp = ollama.chat(model=llm_model, messages=messages, options=options)

        content = resp["message"]["content"]

        return LLMResponse(
            input_tokens=resp["prompt_eval_count"] or 0,
            output_tokens=resp["eval_count"] or 0,
            response=content,
            llm_model=llm_model,
        )
