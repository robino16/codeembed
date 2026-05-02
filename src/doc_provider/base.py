from abc import ABC, abstractmethod
from typing import Iterator

from src.doc_provider.models import Document


class DocProviderBase(ABC):
    @abstractmethod
    def iter(self) -> Iterator[Document]:
        pass
