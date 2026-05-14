import os
import subprocess
from datetime import datetime, timezone
from typing import Iterator, List

from codeembed.doc_provider.base import DocProviderBase
from codeembed.doc_provider.models import DocumentContent, DocumentMeta

# protect users
_SKIP_KEYWORDS = {
    "__init__",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
}


def _get_git_files(base_path: str) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=base_path,
        capture_output=True,
        text=True,
    )
    return set(result.stdout.splitlines())


class LocalDocProvider(DocProviderBase):
    def __init__(self, base_path: str, supported_file_extensions: List[str]) -> None:
        self._base_path = base_path
        self._supported_file_extensions = [ext.lower().split(".")[-1] for ext in supported_file_extensions]

    def iter(self) -> Iterator[DocumentMeta]:

        file_paths = _get_git_files(self._base_path)

        for file_path in file_paths:
            ext = file_path.split(".")[-1]
            if ext.lower() not in self._supported_file_extensions:
                continue

            if any(keyword in file_path for keyword in _SKIP_KEYWORDS):
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
