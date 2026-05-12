from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class CodeEmbedConfig:
    debounce: int
    sleep_interval: int
    llm_model: str
    provider: Literal["ollama", "openai"] = "ollama"
    llm_endpoint: Optional[str] = None
    llm_api_key_env_var: str = "OPENAI_API_KEY"
    use_azure_ad: bool = True
