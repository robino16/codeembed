from typing import Optional

from codeprism.doc_splitters.base import FileSplitterBase
from codeprism.doc_splitters.python_splitter import PythonFileSplitter


class DocSplitterFactory:
    @staticmethod
    def create(file_extension: str) -> Optional[FileSplitterBase]:
        """
        Returns file splitter for the specified file extension.
        Returns None if splitter has not been implemented yet.
        """
        file_extension = file_extension.split(".")[-1].lower()
        if file_extension == "py":
            return PythonFileSplitter()
