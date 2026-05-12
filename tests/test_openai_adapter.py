from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from codeembed.llm.models import ChatMessage
from codeembed.llm.openai_adapter import OpenAILLMService


class _Output(BaseModel):
    summary: str


_MESSAGES: list[ChatMessage] = [{"role": "user", "content": "summarize this"}]
_MODEL = "gpt-4o"


def test_generate_response_returns_content():
    client = MagicMock()
    client.chat.completions.create.return_value.choices = [MagicMock(message=MagicMock(content="hello world"))]

    result = OpenAILLMService(client).generate_response(_MESSAGES, _MODEL)

    assert result == "hello world"
    client.chat.completions.create.assert_called_once_with(messages=_MESSAGES, model=_MODEL)


def test_generate_response_raises_on_none_content():
    client = MagicMock()
    client.chat.completions.create.return_value.choices = [MagicMock(message=MagicMock(content=None))]

    with pytest.raises(ValueError, match="did not return a response"):
        OpenAILLMService(client).generate_response(_MESSAGES, _MODEL)


def test_generate_structured_output_returns_parsed():
    expected = _Output(summary="nice code")
    client = MagicMock()
    client.beta.chat.completions.parse.return_value.choices = [MagicMock(message=MagicMock(parsed=expected))]

    result = OpenAILLMService(client).generate_structured_output(_MESSAGES, _MODEL, _Output)

    assert result == expected
    client.beta.chat.completions.parse.assert_called_once_with(
        messages=_MESSAGES, model=_MODEL, response_format=_Output
    )


def test_generate_structured_output_raises_on_none_parsed():
    client = MagicMock()
    client.beta.chat.completions.parse.return_value.choices = [MagicMock(message=MagicMock(parsed=None))]

    with pytest.raises(ValueError, match="did not return structured output"):
        OpenAILLMService(client).generate_structured_output(_MESSAGES, _MODEL, _Output)
