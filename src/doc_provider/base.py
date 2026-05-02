from abc import ABC, abstractmethod
from typing import Iterator

from src.doc_provider.models import DocumentMeta


class DocProviderBase(ABC):
    @abstractmethod
    def iter(self) -> Iterator[DocumentMeta]:
        """Iterates metadata of files."""

    @abstractmethod
    def get_content(self, file_path: str) -> str:
        """Gets the actual file content."""
