from dataclasses import dataclass
from typing import Dict
from uuid import UUID

from src.types import CommonType


@dataclass
class Chunk:
    id: UUID
    content: str
    metadata: Dict[str, CommonType]
