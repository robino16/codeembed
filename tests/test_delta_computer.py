from datetime import datetime, timedelta
from uuid import uuid4

from src.delta_computer.delta_computer import DeltaComputer
from src.doc_provider.base import DocProviderBase
from src.doc_provider.models import Document
from src.vector_db.base import VectorDbBase
from src.vector_db.models import Chunk


class FakeDocProvider(DocProviderBase):
    def __init__(self, docs):
        self._docs = docs

    def iter(self):
        return iter(self._docs)


class FakeVectorDb(VectorDbBase):
    def __init__(self, chunks):
        self._chunks = chunks

    def iter_chunks(self):
        return iter(self._chunks)

    def search(self, *args, **kwargs):
        raise NotImplementedError()

    def add_chunks(self, *args, **kwargs):
        raise NotImplementedError()


def test_detects_new_document():
    now = datetime.now()

    doc_provider = FakeDocProvider(
        [
            Document(file_path="file1.txt", content="", modified_at=now),
        ]
    )

    vector_db = FakeVectorDb([])

    dc = DeltaComputer(doc_provider, vector_db)
    to_delete, to_update = dc.compute_deltas()

    assert to_delete == set()
    assert to_update == {"file1.txt"}


def test_detects_deleted_document():
    now = datetime.now()

    doc_provider = FakeDocProvider([])

    vector_db = FakeVectorDb(
        [Chunk(id=uuid4(), content="", file_path="file1.txt", modified_at=now)]
    )

    dc = DeltaComputer(doc_provider, vector_db)
    to_delete, to_update = dc.compute_deltas()

    assert to_delete == {"file1.txt"}
    assert to_update == set()


def test_detects_updated_document():
    now = datetime.now()
    older = now - timedelta(days=1)

    doc_provider = FakeDocProvider(
        [
            Document(file_path="file1.txt", content="", modified_at=now),
        ]
    )

    vector_db = FakeVectorDb(
        [
            Chunk(
                id=uuid4(),
                content="",
                file_path="file1.txt",
                modified_at=older,
            )
        ]
    )

    dc = DeltaComputer(doc_provider, vector_db)
    to_delete, to_update = dc.compute_deltas()

    assert to_delete == set()
    assert to_update == {"file1.txt"}
