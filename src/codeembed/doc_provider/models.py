from dataclasses import dataclass
from datetime import datetime

from codeembed.utils.checksum_utils import string_to_sha256


@dataclass
class DocumentMeta:
    file_path: str
    modified_at: datetime


@dataclass
class DocumentContent:
    content: str
    modified_at: datetime

    @property
    def sha256_checksum(self) -> str:
        return string_to_sha256(self.content)
