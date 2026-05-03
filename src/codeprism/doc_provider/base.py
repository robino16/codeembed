from abc import ABC, abstractmethod
from typing import Iterator

from codeprism.doc_provider.models import DocumentContent, DocumentMeta


class DocProviderBase(ABC):
    @abstractmethod
    def iter(self) -> Iterator[DocumentMeta]:
        """Iterates metadata of files."""

    @abstractmethod
    def get_content(self, file_path: str) -> DocumentContent:
        """Gets the actual file content."""
