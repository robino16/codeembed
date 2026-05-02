from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Chunk:
    id: UUID
    content: str
    modified_at: datetime
    file_path: str
