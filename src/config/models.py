from dataclasses import dataclass

from pydantic import BaseModel


class CodebaseEmbedderConfig(BaseModel):
    llm_model: str
    debounce: int
