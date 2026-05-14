from unittest.mock import MagicMock

import pytest
from openai._types import omit
from pydantic import BaseModel

from codeembed.llm.models import ChatMessage
from codeembed.llm.openai_adapter import OpenAILLMService


class _Output(BaseModel):
    summary: str


_MESSAGES: list[ChatMessage] = [{"role": "user", "content": "summarize this"}]
_MODEL = "gpt-4o"


def test_generate_response_returns_content():
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content="hello world"))]
    completion.usage.prompt_tokens = 10
    completion.usage.completion_tokens = 5
    client = MagicMock()
    client.chat.completions.create.return_value = completion

    result = OpenAILLMService(client).generate_response(_MESSAGES, _MODEL)

    assert result.response == "hello world"
    assert result.input_tokens == 10
    assert result.output_tokens == 5
    assert result.llm_model == _MODEL
    client.chat.completions.create.assert_called_once_with(
        messages=_MESSAGES,
        model=_MODEL,
        max_tokens=omit,
        max_completion_tokens=omit,
        temperature=omit,
        response_format={"type": "text"},
    )


def test_generate_response_raises_on_none_content():
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content=None))]
    client = MagicMock()
    client.chat.completions.create.return_value = completion

    with pytest.raises(ValueError, match="did not return a response"):
        OpenAILLMService(client).generate_response(_MESSAGES, _MODEL)


def test_generate_structured_output_returns_parsed():
    expected = _Output(summary="nice code")
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(parsed=expected))]
    completion.usage.prompt_tokens = 20
    completion.usage.completion_tokens = 8
    client = MagicMock()
    client.beta.chat.completions.parse.return_value = completion

    result = OpenAILLMService(client).generate_structured_output(_MESSAGES, _MODEL, _Output)

    assert result.data == expected
    assert result.input_tokens == 20
    assert result.output_tokens == 8
    assert result.llm_model == _MODEL
    client.beta.chat.completions.parse.assert_called_once_with(
        messages=_MESSAGES,
        model=_MODEL,
        response_format=_Output,
        max_tokens=omit,
        max_completion_tokens=omit,
        temperature=omit,
    )


def test_generate_structured_output_raises_on_none_parsed():
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(parsed=None))]
    client = MagicMock()
    client.beta.chat.completions.parse.return_value = completion

    with pytest.raises(ValueError, match="did not return structured output"):
        OpenAILLMService(client).generate_structured_output(_MESSAGES, _MODEL, _Output)
