from dataclasses import dataclass
from typing import Literal

SegmentType = Literal["function", "class", "section"]


@dataclass
class FileSegment:
    line_start: int
    line_end: int
    content: str
    type: SegmentType
