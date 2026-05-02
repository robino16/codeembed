from abc import ABC, abstractmethod
from typing import Dict, List, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMServiceBase(ABC):
    @abstractmethod
    def generate_structured_output(
        self, messages: List[Dict[str, str]], llm_model: str, output_format: Type[T]
    ) -> T:
        pass

    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]], llm_model: str) -> str:
        pass
