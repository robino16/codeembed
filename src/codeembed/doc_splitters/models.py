from dataclasses import dataclass
from typing import List, Literal

SegmentType = Literal["function", "class", "section"]


@dataclass
class FileSegment:
    line_start: int
    line_end: int
    content: str
    type: SegmentType


@dataclass
class SplittedFile:
    file_path: str
    full_content: str
    segments: List[FileSegment]
