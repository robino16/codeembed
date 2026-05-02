import os
from datetime import datetime, timezone
from typing import Iterator, List

from src.doc_provider.base import DocProviderBase
from src.doc_provider.models import DocumentMeta


class LocalDocProvider(DocProviderBase):
    def __init__(
        self, base_path: str, supported_extensions: List[str], skip_keywords: List[str]
    ) -> None:
        self._base_path = base_path
        self._supported_extensions = [
            ext.lower().split(".")[-1] for ext in supported_extensions
        ]
        self._skip_keywords = skip_keywords

    def iter(self) -> Iterator[DocumentMeta]:
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
                    modified_ts = os.path.getmtime(file_path)
                    modified_at = datetime.fromtimestamp(modified_ts, tz=timezone.utc)
                except OSError:
                    # Skip files we can't stat
                    continue

                yield DocumentMeta(
                    file_path=file_path,
                    modified_at=modified_at,
                )

    def get_content(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
