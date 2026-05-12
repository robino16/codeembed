from typing import List, Type, TypeVar, cast

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel

from codeembed.llm.base import LLMServiceBase
from codeembed.llm.models import ChatMessage

T = TypeVar("T", bound=BaseModel)


class OpenAILLMService(LLMServiceBase):
    def __init__(self, client: OpenAI):
        self._client = client

    def generate_structured_output(
        self,
        messages: List[ChatMessage],
        llm_model: str,
        output_format: Type[T],
    ) -> T:

        openai_messages = cast(List[ChatCompletionMessageParam], messages)

        completion = self._client.beta.chat.completions.parse(
            messages=openai_messages,
            model=llm_model,
            response_format=output_format,
        )

        parsed = completion.choices[0].message.parsed

        if parsed is None:
            raise ValueError("LLM did not return structured output")

        return parsed

    def generate_response(
        self,
        messages: List[ChatMessage],
        llm_model: str,
    ) -> str:

        openai_messages = cast(List[ChatCompletionMessageParam], messages)

        completion = self._client.chat.completions.create(
            messages=openai_messages,
            model=llm_model,
        )

        response = completion.choices[0].message.content

        if response is None:
            raise ValueError("LLM did not return a response")

        return response
