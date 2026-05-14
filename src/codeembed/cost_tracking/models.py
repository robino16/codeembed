import json
import os
from typing import Dict, Literal, Optional

from codeembed.utils.time_utils import utc_now

_SessionData = Dict[str, Dict[Literal["input_tokens", "output_tokens", "embedding_tokens"], int]]

_SESSIONS_DIR = ".codeembed/sessions"


class Session:
    def __init__(self):
        self._by_model: _SessionData = {}
        self._session_id = utc_now().strftime("%Y-%m-%dT%H-%M-%S")

    def add(
        self,
        model_name: str,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
    ) -> None:
        if model_name not in self._by_model:
            self._by_model[model_name] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "embedding_tokens": 0,
            }
        if input_tokens is not None:
            self._by_model[model_name]["input_tokens"] += input_tokens
        if output_tokens is not None:
            self._by_model[model_name]["output_tokens"] += output_tokens

    def save(self) -> None:
        if not self._by_model:
            return
        os.makedirs(_SESSIONS_DIR, exist_ok=True)
        with open(f"{_SESSIONS_DIR}/{self._session_id}.json", "w") as f:
            f.write(json.dumps(self._by_model, indent=2))

    def get_usage(self) -> _SessionData:
        return self._by_model

    @property
    def input_tokens(self) -> int:
        return sum(tokens["input_tokens"] for tokens in self._by_model.values())

    @property
    def output_tokens(self) -> int:
        return sum(tokens["output_tokens"] for tokens in self._by_model.values())
