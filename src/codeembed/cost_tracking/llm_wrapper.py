from typing import TypeVar

from pydantic import BaseModel

from codeembed.cost_tracking.models import Session
from codeembed.llm.base import LLMServiceBase
from codeembed.llm.models import LLMResponse, StructuredLLMResponse

T = TypeVar("T", bound=BaseModel)


class LLMServiceWithCostTracking(LLMServiceBase):
    def __init__(self, llm_service: LLMServiceBase, session: Session) -> None:
        self._llm_service = llm_service
        self._session = session

    def generate_structured_output(self, *args, **kwargs) -> StructuredLLMResponse[T]:
        res = self._llm_service.generate_structured_output(*args, **kwargs)

        self._session.add(
            model_name=res.llm_model,
            input_tokens=res.input_tokens,
            output_tokens=res.output_tokens,
        )

        return res

    def generate_response(self, *args, **kwargs) -> LLMResponse:
        res = self._llm_service.generate_response(*args, **kwargs)

        self._session.add(
            model_name=res.llm_model,
            input_tokens=res.input_tokens,
            output_tokens=res.output_tokens,
        )

        return res
