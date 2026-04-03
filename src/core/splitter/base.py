from abc import ABC, abstractmethod

from src.core.splitter.value_objects import SplittedFile


class FileSpliterBase(ABC):

    @abstractmethod
    def split_file(self, file_path: str, content: str) -> SplittedFile:
        pass
