from unittest.mock import MagicMock

from pydantic import BaseModel

from codeembed.cost_tracking.llm_wrapper import LLMServiceWithCostTracking
from codeembed.cost_tracking.models import Session
from codeembed.llm.models import LLMResponse, StructuredLLMResponse


class _Output(BaseModel):
    summary: str


def test_session_accumulates_tokens_for_same_model():
    session = Session()
    session.add("gpt-4o", input_tokens=100, output_tokens=50)
    session.add("gpt-4o", input_tokens=200, output_tokens=30)

    assert session.input_tokens == 300
    assert session.output_tokens == 80


def test_session_accumulates_tokens_across_models():
    session = Session()
    session.add("gpt-4o", input_tokens=100, output_tokens=50)
    session.add("llama3", input_tokens=40, output_tokens=10)

    assert session.input_tokens == 140
    assert session.output_tokens == 60


def test_session_ignores_none_tokens():
    session = Session()
    session.add("gpt-4o", input_tokens=None, output_tokens=None)

    assert session.input_tokens == 0
    assert session.output_tokens == 0


def test_session_save_skips_when_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = Session()
    session.save()

    assert not (tmp_path / ".codeembed" / "sessions").exists()


def test_session_save_creates_directory_and_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = Session()
    session.add("gpt-4o", input_tokens=10, output_tokens=5)
    session.save()

    sessions_dir = tmp_path / ".codeembed" / "sessions"
    assert sessions_dir.exists()
    files = list(sessions_dir.iterdir())
    assert len(files) == 1
    assert files[0].suffix == ".json"


def test_session_filename_has_no_colons(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    session = Session()
    session.add("gpt-4o", input_tokens=1, output_tokens=1)
    session.save()

    files = list((tmp_path / ".codeembed" / "sessions").iterdir())
    assert ":" not in files[0].name


def test_llm_wrapper_tracks_generate_response():
    inner = MagicMock()
    inner.generate_response.return_value = LLMResponse(
        input_tokens=50, output_tokens=20, response="ok", llm_model="gpt-4o"
    )
    session = Session()

    LLMServiceWithCostTracking(inner, session).generate_response([], "gpt-4o")

    assert session.input_tokens == 50
    assert session.output_tokens == 20


def test_llm_wrapper_tracks_generate_structured_output():
    inner = MagicMock()
    inner.generate_structured_output.return_value = StructuredLLMResponse(
        input_tokens=80, output_tokens=30, data=_Output(summary="x"), llm_model="gpt-4o"
    )
    session = Session()

    LLMServiceWithCostTracking(inner, session).generate_structured_output([], "gpt-4o", _Output)

    assert session.input_tokens == 80
    assert session.output_tokens == 30


def test_llm_wrapper_returns_original_response():
    response = LLMResponse(input_tokens=5, output_tokens=2, response="hello", llm_model="gpt-4o")
    inner = MagicMock()
    inner.generate_response.return_value = response
    session = Session()

    result = LLMServiceWithCostTracking(inner, session).generate_response([], "gpt-4o")

    assert result is response
