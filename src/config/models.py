from dataclasses import dataclass


@dataclass
class CodePrismConfig:
    llm_model: str
    debounce: int
    sleep_interval: int
