from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class CodeEmbedConfig:
    debounce: int
    sleep_interval: int
    llm_model: str
    provider: Literal["ollama", "openai"] = "ollama"
    llm_api_endpoint_env_var: Optional[str] = None
    llm_api_key_env_var: Optional[str] = None
    env_var_path: Optional[str] = None
