from core.splitter.base import FileSpliterBase
from core.splitter.value_objects import FileSegment, SplittedFile


class PythonFileSplitter(FileSpliterBase):

    def split_file(self, file_path: str, content: str) -> SplittedFile:
        lines = content.splitlines(keepends=True)
        n = len(lines)

        segments = []

        def indent_of(line: str):
            stripped = line.strip()
            if not stripped:
                return None
            return len(line) - len(line.lstrip())

        # Find top-level blocks: class/def at indent 0
        block_starts = []
        for i, line in enumerate(lines):
            ind = indent_of(line)
            if ind == 0:
                if line.startswith("class "):
                    block_starts.append((i, "class"))
                elif line.startswith("def "):
                    block_starts.append((i, "function"))

        top_start = block_starts[0][0] if block_starts else n
        if top_start > 0:
            segments.append(
                FileSegment(
                    line_start=1,
                    line_end=top_start,
                    content="".join(lines[:top_start]),
                    type="top",
                )
            )

        for j, (start, btype) in enumerate(block_starts):
            end = block_starts[j + 1][0] if j + 1 < len(block_starts) else n
            seg_lines = lines[start:end]
            seg = FileSegment(
                line_start=start + 1,
                line_end=end,
                content="".join(seg_lines),
                type=btype,
            )
            segments.append(seg)

            if btype == "class":
                # Determine method indent from the first non-empty indented line
                method_indent = None
                for line in seg_lines:
                    ind = indent_of(line)
                    if ind is not None and ind > 0:
                        method_indent = ind
                        break

                if method_indent is not None:
                    method_starts = [
                        k
                        for k, line in enumerate(seg_lines)
                        if indent_of(line) == method_indent
                        and line.lstrip().startswith("def ")
                    ]
                    for m, mstart in enumerate(method_starts):
                        mend = (
                            method_starts[m + 1]
                            if m + 1 < len(method_starts)
                            else len(seg_lines)
                        )
                        segments.append(
                            FileSegment(
                                line_start=start + mstart + 1,
                                line_end=start + mend,
                                content="".join(seg_lines[mstart:mend]),
                                type="method",
                            )
                        )

        return SplittedFile(
            file_path=file_path,
            content=content,
            segments=segments,
        )


class MarkdownFileSplitter(FileSpliterBase):

    def split_file(self, file_path: str, content: str) -> SplittedFile:
        lines = content.splitlines(keepends=True)
        n = len(lines)

        # Find lines that start a new ## section
        section_starts = [i for i, line in enumerate(lines) if line.startswith("## ")]

        segments = []
        if not section_starts:
            # No ## headings — whole file is one segment
            segments.append(
                FileSegment(line_start=1, line_end=n, content=content, type="section")
            )
        else:
            # Preamble (# title + any text before first ##) merged into first section
            limits = section_starts + [n]
            for j, sec_start in enumerate(section_starts):
                actual_start = 0 if j == 0 else sec_start
                end = limits[j + 1]
                segments.append(
                    FileSegment(
                        line_start=actual_start + 1,
                        line_end=end,
                        content="".join(lines[actual_start:end]),
                        type="section",
                    )
                )

        return SplittedFile(
            file_path=file_path,
            content=content,
            segments=segments,
        )
