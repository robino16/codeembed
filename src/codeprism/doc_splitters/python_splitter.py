from typing import List

from codeprism.doc_splitters.base import FileSplitterBase
from codeprism.doc_splitters.models import FileSegment, SegmentType


def _extract_generic(file_content: str, segment_type: SegmentType) -> List[FileSegment]:
    keyword = "class" if segment_type == "class" else "def"
    segments = []
    current_lines = []
    is_candidate = False
    in_multiline_string = False
    multiline_delimiter = None
    line_start = 0
    lines = file_content.splitlines()

    for i, line in enumerate(lines):
        # Track multiline string boundaries
        stripped = line
        for delim in ('"""', "'''"):
            count = stripped.count(delim)
            if count > 0:
                if not in_multiline_string:
                    # Odd number of delimiters means we're opening a block
                    if count % 2 == 1:
                        in_multiline_string = True
                        multiline_delimiter = delim
                else:
                    if delim == multiline_delimiter and count % 2 == 1:
                        in_multiline_string = False
                        multiline_delimiter = None

        if not is_candidate and line.startswith(f"{keyword} "):
            line_start = i + 1
            is_candidate = True

        is_last_line = i == len(lines) - 1
        if (
            is_candidate
            and not in_multiline_string
            and line_start != i + 1
            and ((not line.startswith((" ", "\t", "\n"))) or is_last_line)
        ):
            line_end = i + 1
            class_content = "\n".join(current_lines)
            if is_last_line:
                class_content += "\n" + line
            current_lines = []
            segments.append(
                FileSegment(
                    content=class_content,
                    line_start=line_start,
                    line_end=line_end,
                    type=segment_type,
                )
            )
            is_candidate = False

        if is_candidate:
            current_lines.append(line)

    return segments


class PythonFileSplitter(FileSplitterBase):
    def split_file(self, file_content: str) -> List[FileSegment]:
        # we only care about functions and classes for now
        classes = _extract_generic(file_content, "class")
        functions = _extract_generic(file_content, "function")
        return classes + functions
