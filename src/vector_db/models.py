from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class Chunk:
    id: UUID
    content: str
    modified_at: datetime
    file_path: str
    line_start: int
    line_end: int
    raw_code: Optional[str]
    file_sha256_checksum: str
