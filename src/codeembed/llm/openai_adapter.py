from typing import List, Optional, Type, TypeVar, cast

from openai import OpenAI
from openai._types import omit
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from codeembed.llm.base import LLMServiceBase
from codeembed.llm.models import ChatMessage, LLMResponse, StructuredLLMResponse

T = TypeVar("T", bound=BaseModel)


class OpenAILLMService(LLMServiceBase):
    def __init__(self, client: OpenAI):
        self._client = client

    def generate_structured_output(
        self,
        messages: List[ChatMessage],
        llm_model: str,
        output_format: Type[T],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> StructuredLLMResponse[T]:

        openai_messages = cast(List[ChatCompletionMessageParam], messages)

        # newer OpenAI models requires max_completion_tokens instead of max_tokens...
        _max_tokens = max_tokens if max_tokens is not None else omit
        max_completion_tokens = omit
        if self._is_reasoning_model(llm_model):
            max_completion_tokens = _max_tokens
            _max_tokens = omit

        completion = self._client.beta.chat.completions.parse(
            messages=openai_messages,
            model=llm_model,
            response_format=output_format,
            max_tokens=_max_tokens,
            max_completion_tokens=max_completion_tokens,
            temperature=temperature if temperature is not None else omit,
        )

        parsed = completion.choices[0].message.parsed

        if parsed is None:
            raise ValueError("LLM did not return structured output")

        return StructuredLLMResponse(
            input_tokens=completion.usage.prompt_tokens if completion.usage else 0,
            output_tokens=completion.usage.completion_tokens if completion.usage else 0,
            model=parsed,
            llm_model=llm_model,
        )

    def generate_response(
        self,
        messages: List[ChatMessage],
        llm_model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:

        openai_messages = cast(List[ChatCompletionMessageParam], messages)

        # newer OpenAI models requires max_completion_tokens instead of max_tokens...
        _max_tokens = max_tokens if max_tokens is not None else omit
        max_completion_tokens = omit
        if self._is_reasoning_model(llm_model):
            max_completion_tokens = _max_tokens
            _max_tokens = omit

        completion = self._client.chat.completions.create(
            messages=openai_messages,
            model=llm_model,
            max_tokens=_max_tokens,
            max_completion_tokens=max_completion_tokens,
            temperature=temperature if temperature is not None else omit,
            response_format={"type": "text"},
        )

        response = completion.choices[0].message.content

        if response is None:
            raise ValueError("LLM did not return a response")

        return LLMResponse(
            input_tokens=completion.usage.prompt_tokens if completion.usage else 0,
            output_tokens=completion.usage.completion_tokens if completion.usage else 0,
            response=response,
            llm_model=llm_model,
        )

    def _is_reasoning_model(self, llm_model: str) -> bool:
        return not llm_model.startswith("gpt-4") and not llm_model.startswith("gpt-3")
