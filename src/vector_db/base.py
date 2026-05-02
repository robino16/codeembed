from abc import ABC, abstractmethod
from typing import Iterator, List

from src.vector_db.models import Chunk


class VectorDbBase(ABC):
    @abstractmethod
    def add_chunks(self, chunks: List[Chunk]) -> None:
        pass

    @abstractmethod
    def search(self, query: str, top_n: int) -> List[Chunk]:
        """Vector search. Returns top_n most relevant results."""

    @abstractmethod
    def iter_chunks(self) -> Iterator[Chunk]:
        """Iterates all chunks stored in the vector database."""
