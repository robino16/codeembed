import os
from datetime import datetime, timezone
import subprocess
from typing import Iterator, List

from src.doc_provider.base import DocProviderBase
from src.doc_provider.models import DocumentContent, DocumentMeta

# By default we skip some common folders and files.
# For extra safety.
_DEFAULT_SKIP_KEYWORDS = [
    "venv",
    "pytest_cache",
    "node_modules",
    ".env",
    ".env.local",
    "dist",
    "build",
]


def _get_git_files(base_path: str) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=base_path,
        capture_output=True,
        text=True,
    )
    return set(result.stdout.splitlines())


class LocalDocProvider(DocProviderBase):
    def __init__(
        self, base_path: str, supported_file_extensions: List[str], extra_skip_keywords: List[str]
    ) -> None:
        self._base_path = base_path
        self._supported_file_extensions = [
            ext.lower().split(".")[-1] for ext in supported_file_extensions
        ]
        self._skip_keywords = [kw.lower() for kw in extra_skip_keywords] + _DEFAULT_SKIP_KEYWORDS

    def iter(self) -> Iterator[DocumentMeta]:

        file_paths = _get_git_files(self._base_path)

        for file_path in file_paths:

            ext = file_path.split(".")[-1]
            if ext.lower() not in self._supported_file_extensions:
                continue

            # we skip here to avoid loading unecessary documents
            skip = False
            for skip_kw in self._skip_keywords:
                if skip_kw in file_path.lower():
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

    def get_content(self, file_path: str) -> DocumentContent:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        modified_ts = os.path.getmtime(file_path)
        modified_at = datetime.fromtimestamp(modified_ts, tz=timezone.utc)
        return DocumentContent(content=content, modified_at=modified_at)
