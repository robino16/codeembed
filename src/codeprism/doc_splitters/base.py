from abc import ABC, abstractmethod
from typing import List

from codeprism.doc_splitters.models import FileSegment


class FileSplitterBase(ABC):
    @abstractmethod
    def split_file(self, file_content: str) -> List[FileSegment]:
        pass
