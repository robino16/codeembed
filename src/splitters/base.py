from abc import ABC, abstractmethod

from src.models.splitted_file import SplittedFile


class FileSplitterBase(ABC):
    @abstractmethod
    def split_file(self, content: str) -> SplittedFile:
        pass
