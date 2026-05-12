from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class CodeEmbedConfig:
    debounce: int
    sleep_interval: int
    llm_model: str
    provider: Literal["ollama", "openai"] = "ollama"
    # Protect endpoint in env. vars by default to protect users.
    llm_api_endpoint_env_var: Optional[str] = "OPENAI_BASE_URL"
    llm_api_key_env_var: str = "OPENAI_API_KEY"
    env_var_path: Optional[str] = None
