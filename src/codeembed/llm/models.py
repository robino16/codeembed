from dataclasses import dataclass
from typing import Generic, Literal, TypedDict, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ChatMessage(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class LLMResponse:
    input_tokens: int
    output_tokens: int
    response: str
    llm_model: str


@dataclass
class StructuredLLMResponse(Generic[T]):
    input_tokens: int
    output_tokens: int
    data: T
    llm_model: str
