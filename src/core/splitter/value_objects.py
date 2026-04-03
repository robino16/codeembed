from dataclasses import dataclass
from typing import List, Literal


SegmentType = Literal["function", "method", "class", "section", "top"]


@dataclass
class FileSegment:
    line_start: int
    line_end: int
    content: str
    type: SegmentType


@dataclass
class SplittedFile:
    file_path: str
    content: str
    segments: List[FileSegment]
