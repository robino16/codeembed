from abc import ABC, abstractmethod
from typing import List

from src.vector_db.models import Chunk


class VectorDbBase(ABC):
    @abstractmethod
    def add_chunks(self, chunks: List[Chunk]) -> None:
        pass

    @abstractmethod
    def search(self, query: str, top_n: int) -> List[Chunk]:
        pass
