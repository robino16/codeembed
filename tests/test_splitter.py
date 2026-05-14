from codeembed.doc_splitters.generic_splitter import FileSplitter, _detect_splits

splitter = FileSplitter(max_tokens=512, overlap_lines=3)


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

_MD = """\
# My Project

Some intro text.

## Installation

Install with pip.

## Usage

Run the command.
"""


def test_markdown_produces_three_segments():
    segments = splitter.split_file(_MD, "README.md")
    assert len(segments) == 3


def test_markdown_preamble_contains_intro():
    segments = splitter.split_file(_MD, "README.md")
    assert "# My Project" in segments[0].content
    assert "Some intro text." in segments[0].content


def test_markdown_second_segment_is_installation():
    segments = splitter.split_file(_MD, "README.md")
    assert "## Installation" in segments[1].content
    assert "Install with pip." in segments[1].content


def test_markdown_third_segment_is_usage():
    segments = splitter.split_file(_MD, "README.md")
    assert "## Usage" in segments[2].content
    assert "Run the command." in segments[2].content


def test_markdown_h3_not_a_split_point():
    content = "## Section\n\n### Subsection\n\ntext\n"
    segments = splitter.split_file(content, "doc.md")
    # ### should NOT split — subsection stays inside the ## chunk
    assert len(segments) == 1
    assert "### Subsection" in segments[0].content


# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

_PY = """\
import os

CONSTANT = 42


def helper():
    return CONSTANT


class MyClass:
    def method(self):
        return 1
"""


def test_python_splits_into_correct_number_of_segments():
    segments = splitter.split_file(_PY, "app.py")
    # preamble, helper, MyClass
    assert len(segments) == 3


def test_python_preamble_contains_import():
    segments = splitter.split_file(_PY, "app.py")
    assert "import os" in segments[0].content


def test_python_function_segment():
    segments = splitter.split_file(_PY, "app.py")
    fn_seg = next(s for s in segments if "def helper" in s.content)
    assert "return CONSTANT" in fn_seg.content


def test_python_class_segment():
    segments = splitter.split_file(_PY, "app.py")
    cls_seg = next(s for s in segments if "class MyClass" in s.content)
    assert "def method" in cls_seg.content


def test_python_decorator_included_in_function_segment():
    content = "import x\n\n\n@staticmethod\ndef compute():\n    return 1\n"
    segments = splitter.split_file(content, "app.py")
    fn_seg = next(s for s in segments if "def compute" in s.content)
    assert "@staticmethod" in fn_seg.content


def test_python_indented_def_not_a_split_point():
    content = "class Foo:\n    def method(self):\n        pass\n"
    segments = splitter.split_file(content, "app.py")
    # only one split (class at col 0), method is indented
    assert len(segments) == 1
    assert "def method" in segments[0].content


# ---------------------------------------------------------------------------
# TypeScript — keyword detection
# ---------------------------------------------------------------------------

_TS = """\
const config = { debug: true };

function helper() {
    return 42;
}

export function main() {
    return helper();
}

export class MyService {
    getValue() {
        return 1;
    }
}
"""


def test_typescript_splits_into_correct_number_of_segments():
    segments = splitter.split_file(_TS, "app.ts")
    # preamble, helper, main, MyService
    assert len(segments) == 4


def test_typescript_preamble_contains_config():
    segments = splitter.split_file(_TS, "app.ts")
    assert "const config" in segments[0].content


def test_typescript_function_segment_contains_body():
    segments = splitter.split_file(_TS, "app.ts")
    helper_seg = next(s for s in segments if "function helper" in s.content)
    assert "return 42" in helper_seg.content


def test_typescript_export_function_segment():
    segments = splitter.split_file(_TS, "app.ts")
    main_seg = next(s for s in segments if "export function main" in s.content)
    assert "return helper()" in main_seg.content


def test_typescript_class_segment():
    segments = splitter.split_file(_TS, "app.ts")
    class_seg = next(s for s in segments if "export class MyService" in s.content)
    assert "getValue" in class_seg.content


def test_typescript_indented_keyword_not_a_split_point():
    # Inner function should not be treated as a top-level split
    content = "function outer() {\n    function inner() {\n        return 1;\n    }\n}\n"
    segments = splitter.split_file(content, "app.ts")
    assert len(segments) == 1
    assert "inner" in segments[0].content


# ---------------------------------------------------------------------------
# Decorator and comment preservation (backwards scan)
# ---------------------------------------------------------------------------

_TS_WITH_DECORATOR = """\
const VERSION = "1.0";

@Injectable()
export class MyService {
    getValue() {
        return 42;
    }
}
"""


def test_decorator_included_in_class_segment():
    segments = splitter.split_file(_TS_WITH_DECORATOR, "service.ts")
    class_seg = next(s for s in segments if "export class MyService" in s.content)
    assert "@Injectable()" in class_seg.content


_TS_WITH_COMMENT = """\
const x = 1;

// computes the answer
function compute() {
    return 42;
}
"""


def test_comment_above_function_included_in_segment():
    segments = splitter.split_file(_TS_WITH_COMMENT, "util.ts")
    fn_seg = next(s for s in segments if "function compute" in s.content)
    assert "// computes the answer" in fn_seg.content


# ---------------------------------------------------------------------------
# Line numbers
# ---------------------------------------------------------------------------


def test_markdown_line_numbers_are_correct():
    segments = splitter.split_file(_MD, "README.md")
    # Preamble starts at 0
    assert segments[0].line_start == 0
    # Each segment's line_end equals the next one's keyword line
    for i in range(len(segments) - 1):
        assert (
            segments[i].line_end == segments[i + 1].line_start or segments[i].line_end >= segments[i + 1].line_start
        )  # overlap allowed


def test_line_start_less_than_line_end():
    for path, content in [("README.md", _MD), ("app.ts", _TS)]:
        for seg in splitter.split_file(content, path):
            assert seg.line_start < seg.line_end, f"Empty segment in {path}: {seg}"


# ---------------------------------------------------------------------------
# Fixed-length fallback (unknown extension)
# ---------------------------------------------------------------------------


def test_unknown_extension_returns_segments():
    content = "\n".join(f"line {i}" for i in range(200))
    segments = splitter.split_file(content, "file.xyz")
    assert len(segments) > 1


def test_fixed_length_overlap_content_appears_in_consecutive_chunks():
    # Generate content large enough to force multiple chunks
    content = "\n".join(f"word{i} " * 20 for i in range(100))
    segments = splitter.split_file(content, "file.xyz")
    assert len(segments) >= 2
    # Last lines of chunk N should appear in chunk N+1 (overlap)
    last_line_of_first = segments[0].content.splitlines()[-1]
    assert last_line_of_first in segments[1].content


def test_fixed_length_line_numbers_with_offset():
    content = "\n".join(f"word{i} " * 20 for i in range(100))
    segments = splitter.split_file(content, "file.xyz")
    # line_start of second chunk should be less than line_end of first (overlap)
    assert segments[1].line_start < segments[0].line_end


# ---------------------------------------------------------------------------
# _detect_splits unit tests
# ---------------------------------------------------------------------------


def test_detect_splits_always_starts_at_zero():
    content = "preamble\n\ndef foo():\n    pass\n"
    lines = _detect_splits(content, ["def "])
    assert lines[0] == 0


def test_detect_splits_finds_keyword_lines():
    content = "import x\n\ndef foo():\n    pass\n\ndef bar():\n    pass\n"
    lines = _detect_splits(content, ["def "])
    assert 2 in lines  # def foo
    assert 5 in lines  # def bar


def test_detect_splits_ignores_indented_keywords():
    content = "def outer():\n    def inner():\n        pass\n"
    lines = _detect_splits(content, ["def "])
    assert 1 not in lines  # inner() is indented, should not be a split
