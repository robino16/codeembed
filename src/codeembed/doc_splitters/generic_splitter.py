from typing import Dict, List

import tiktoken

from codeembed.doc_splitters.models import FileSegment

_encoder = tiktoken.get_encoding("o200k_base")

_SPLIT_KEYWORDS: Dict[str, List[str]] = {
    "py": ["class ", "def "],
    "md": ["## "],
    "ts": [
        "export function ",
        "export class ",
        "export const ",
        "export interface ",
        "export type ",
        "export default ",
        "function ",
        "class ",
    ],
    "tsx": [
        "export function ",
        "export class ",
        "export const ",
        "export interface ",
        "export type ",
        "export default ",
        "function ",
        "class ",
    ],
    "js": ["export function ", "export class ", "export const ", "export default ", "function ", "class "],
    "jsx": ["export function ", "export class ", "export const ", "export default ", "function ", "class "],
}


def _count_tokens(text: str) -> int:
    return len(_encoder.encode(text))


def _split_by_fixed_length(
    content: str,
    max_tokens: int = 512,
    overlap_lines: int = 5,
    line_offset: int = 0,
) -> List[FileSegment]:
    lines = content.splitlines()
    chunks: List[FileSegment] = []
    chunk: List[str] = []
    chunk_tokens = 0
    chunk_start = 0

    for i, line in enumerate(lines):
        line_tokens = _count_tokens(line)
        if chunk_tokens + line_tokens > max_tokens and chunk:
            chunks.append(
                FileSegment(
                    line_start=line_offset + chunk_start,
                    line_end=line_offset + i,
                    content="\n".join(chunk),
                )
            )
            overlap = chunk[-overlap_lines:]
            chunk = overlap
            chunk_tokens = sum(_count_tokens(ln) for ln in chunk)
            chunk_start = i - len(overlap)
        chunk.append(line)
        chunk_tokens += line_tokens

    if chunk:
        chunks.append(
            FileSegment(
                line_start=line_offset + chunk_start,
                line_end=line_offset + len(lines),
                content="\n".join(chunk),
            )
        )

    return chunks


def _detect_splits(content: str, split_keywords: List[str]) -> List[int]:
    split_lines = []
    for i, line in enumerate(content.splitlines()):
        for keyword in split_keywords:
            if line.startswith(keyword):
                split_lines.append(i)
                break
    if not split_lines or split_lines[0] != 0:
        split_lines.insert(0, 0)
    return split_lines


def _apply_splits(
    content: str,
    split_lines: List[int],
    max_tokens: int = 512,
    overlap_lines: int = 5,
) -> List[FileSegment]:
    segments = []
    lines = content.splitlines()

    for i in range(len(split_lines)):
        split_start = split_lines[i]
        split_end = split_lines[i + 1] if i + 1 < len(split_lines) else len(lines)

        # Scan backwards to the nearest empty line so decorators/comments are included
        actual_start = split_start
        for j in range(split_start - 1, -1, -1):
            if not lines[j].strip():
                actual_start = j + 1
                break
        else:
            if split_start > 0:
                actual_start = 0

        if actual_start == split_end:
            continue

        segment_content = "\n".join(lines[actual_start:split_end])

        if _count_tokens(segment_content) <= max_tokens:
            segments.append(
                FileSegment(
                    line_start=actual_start,
                    line_end=split_end,
                    content=segment_content,
                )
            )
        else:
            segments.extend(
                _split_by_fixed_length(
                    segment_content,
                    max_tokens=max_tokens,
                    overlap_lines=overlap_lines,
                    line_offset=actual_start,
                )
            )

    return segments


class FileSplitter:
    def __init__(self, max_tokens: int = 512, overlap_lines: int = 5):
        self._max_tokens = max_tokens
        self._overlap_lines = overlap_lines

    def split_file(self, file_content: str, file_path: str) -> List[FileSegment]:

        file_extension = file_path.split(".")[-1].lower()

        if file_extension not in _SPLIT_KEYWORDS:
            return _split_by_fixed_length(
                file_content,
                max_tokens=self._max_tokens,
                overlap_lines=self._overlap_lines,
            )

        split_lines = _detect_splits(file_content, _SPLIT_KEYWORDS[file_extension])
        return _apply_splits(
            file_content,
            split_lines,
            max_tokens=self._max_tokens,
            overlap_lines=self._overlap_lines,
        )
