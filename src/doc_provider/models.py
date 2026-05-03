from dataclasses import dataclass
from datetime import datetime


@dataclass
class DocumentMeta:
    file_path: str
    modified_at: datetime


@dataclass
class DocumentContent:
    content: str
    modified_at: datetime
