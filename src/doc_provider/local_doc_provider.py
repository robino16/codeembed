import os
from datetime import datetime
from typing import Iterator, List

from src.doc_provider.base import DocProviderBase
from src.doc_provider.models import Document


class LocalDocProvider(DocProviderBase):
    def __init__(
        self, base_path: str, supported_extensions: List[str], skip_keywords: List[str]
    ) -> None:
        self._base_path = base_path
        self._supported_extensions = [
            ext.lower().split(".")[-1] for ext in supported_extensions
        ]
        self._skip_keywords = skip_keywords

    def iter(self) -> Iterator[Document]:
        # NOTE: We could split this into two methods,
        #       one for iter_metadata and one for download_document
        #       currently doc provider filters documents
        #       this is a OK for a simple app
        for root, _, files in os.walk(self._base_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)

                ext = file_path.split(".")[-1]
                if ext.lower() not in self._supported_extensions:
                    continue

                # we skip here to avoid loading unecessary documents
                skip = False
                for skip_kw in self._skip_keywords:
                    if skip_kw.lower() in file_path:
                        skip = True
                        break
                if skip:
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except UnicodeDecodeError, OSError:
                    # Skip non-text or unreadable files
                    continue

                try:
                    modified_ts = os.path.getmtime(file_path)
                    modified_at = datetime.fromtimestamp(modified_ts)
                except OSError:
                    # Skip files we can't stat
                    continue

                yield Document(
                    file_path=file_path,
                    content=content,
                    modified_at=modified_at,
                )
