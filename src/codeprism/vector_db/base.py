from abc import ABC, abstractmethod
from typing import Dict, Iterator, List, Optional
from uuid import UUID

from codeprism.vector_db.models import Chunk


class VectorDbBase(ABC):
    @abstractmethod
    def add_chunks(self, chunks: List[Chunk]) -> None:
        pass

    @abstractmethod
    def search(self, query: str, top_n: int) -> List[Chunk]:
        """Vector search. Returns top_n most relevant results."""

    @abstractmethod
    def iter_chunks(self, where: Optional[Dict[str, str]] = None) -> Iterator[Chunk]:
        """
        Iterates all chunks stored in the vector database.

        For simplicity exposes 'where' argument which is a ChromaDB specific filter.
        """

    @abstractmethod
    def delete_chunks(self, chunk_ids: List[UUID]) -> None:
        pass
