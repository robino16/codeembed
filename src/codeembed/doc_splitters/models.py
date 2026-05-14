from dataclasses import dataclass


@dataclass
class FileSegment:
    line_start: int
    line_end: int
    content: str


@dataclass
class SplittedFile:
    file_path: str
    full_content: str
