from src.doc_splitters.python_splitter import PythonFileSplitter


def test_detects_class():

    # Arrange
    file_content = """import pandas as pd
from pydantic import BaseModel

class MyEntity(BaseModel):
    id: str
    age: int
"""

    python_splitter = PythonFileSplitter()

    # Act
    segments = python_splitter.split_file(file_content)

    # Assert
    assert len(segments) == 1
    assert segments[0].content.startswith("class MyEntity(BaseModel):")
    assert segments[0].type == "class"
    assert segments[0].line_start == 4
    assert segments[0].line_end == 6
    assert len(segments[0].content.splitlines()) == 3


def test_detects_two_class():

    # Arrange
    file_content = """import pandas as pd
from pydantic import BaseModel

class MyEntity(BaseModel):
    id: str
    age: int

class SecondEntity(BaseModel):
    id: str
    age: int
"""

    python_splitter = PythonFileSplitter()

    # Act
    segments = python_splitter.split_file(file_content)

    # Assert
    assert len(segments) == 2
    assert segments[0].content.startswith("class MyEntity(BaseModel):")
    assert segments[0].type == "class"
    assert segments[0].line_start == 4
    assert segments[0].line_end == 7
    assert len(segments[0].content.splitlines()) == 3

    assert segments[1].content.startswith("class SecondEntity(BaseModel):")
    assert segments[1].type == "class"
    assert segments[1].line_start == 8
    assert segments[1].line_end == 10
    assert len(segments[1].content.splitlines()) == 3


def test_detects_functions():

    # Arrange
    file_content = """import pandas as pd
from pydantic import BaseModel

def pytagoras(a, b):
    \"\"\"Some text here\"\"\"
    return sqrt(a ** 2 + b ** 2)
"""

    python_splitter = PythonFileSplitter()

    # Act
    segments = python_splitter.split_file(file_content)

    # Assert
    assert len(segments) == 1
    assert segments[0].content.startswith("def pytagoras(a, b):")
    assert segments[0].type == "function"
    assert segments[0].line_start == 4
    assert segments[0].line_end == 6
    assert len(segments[0].content.splitlines()) == 3


def test_ignores_long_string():

    # Arrange
    file_content = """import pandas as pd
from pydantic import BaseModel

def write_something_nice():
    print(\"\"\"
Have a nice day!
\"\"\")
"""

    python_splitter = PythonFileSplitter()

    # Act
    segments = python_splitter.split_file(file_content)

    # Assert
    assert len(segments) == 1
    assert segments[0].content.startswith("def write_something_nice():")
    assert segments[0].type == "function"
    assert segments[0].line_start == 4
    assert segments[0].line_end == 7
    assert len(segments[0].content.splitlines()) == 4
