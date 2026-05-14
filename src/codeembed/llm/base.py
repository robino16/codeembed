from abc import ABC, abstractmethod
from typing import List, Optional, Type, TypeVar

from pydantic import BaseModel

from codeembed.llm.models import ChatMessage, LLMResponse, StructuredLLMResponse

T = TypeVar("T", bound=BaseModel)


class LLMServiceBase(ABC):
    @abstractmethod
    def generate_structured_output(
        self,
        messages: List[ChatMessage],
        llm_model: str,
        output_format: Type[T],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> StructuredLLMResponse[T]:
        pass

    @abstractmethod
    def generate_response(
        self,
        messages: List[ChatMessage],
        llm_model: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        pass
