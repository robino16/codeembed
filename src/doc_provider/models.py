from dataclasses import dataclass
from datetime import datetime


@dataclass
class Document:
    file_path: str
    content: str
    modified_at: datetime
