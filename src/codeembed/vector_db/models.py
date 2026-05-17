from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
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
    graph_node_ids: List[str] = field(default_factory=list)


@dataclass
class SearchResult:
    chunk: Chunk
    score: float
