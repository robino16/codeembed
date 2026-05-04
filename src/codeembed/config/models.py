from dataclasses import dataclass


@dataclass
class CodeEmbedConfig:
    llm_model: str
    debounce: int
    sleep_interval: int
