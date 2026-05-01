from dataclasses import dataclass
from typing import List

from src.models.file_segment import FileSegment


@dataclass
class SplittedFile:
    file_path: str
    full_content: str
    segments: List[FileSegment]
