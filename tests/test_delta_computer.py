from datetime import timedelta
from uuid import uuid4

from codeembed.delta_computer.delta_computer import DeltaComputer
from codeembed.doc_provider.base import DocProviderBase
from codeembed.doc_provider.models import DocumentContent, DocumentMeta
from codeembed.utils.time_utils import utc_now
from codeembed.vector_db.base import VectorDbBase
from codeembed.vector_db.models import Chunk


class FakeDocProvider(DocProviderBase):
    def __init__(self, docs, content_by_path=None):
        self._docs = docs
        self._content_by_path = content_by_path or {}

    def iter(self):
        return iter(self._docs)

    def get_content(self, file_path: str) -> DocumentContent:
        content = self._content_by_path.get(file_path, "")
        return DocumentContent(content=content, modified_at=utc_now())


class FakeVectorDb(VectorDbBase):
    def __init__(self, chunks):
        self._chunks = chunks

    def iter_chunks(self, *args, **kwargs):
        return iter(self._chunks)

    def search(self, *args, **kwargs):
        raise NotImplementedError()

    def add_chunks(self, *args, **kwargs):
        raise NotImplementedError()

    def delete_chunks(self, *args, **kwargs):
        raise NotImplementedError()

    def get_chunks(self, *args, **kwargs):
        raise NotImplementedError()


def test_detects_new_document():
    now = utc_now()

    doc_provider = FakeDocProvider(
        [
            DocumentMeta(file_path="file1.txt", modified_at=now),
        ]
    )

    vector_db = FakeVectorDb([])

    dc = DeltaComputer(doc_provider, vector_db, debounce_seconds=0)
    to_delete, to_update, _ = dc.compute_deltas()

    assert to_delete == set()
    assert to_update == {"file1.txt"}


def test_detects_deleted_document():
    now = utc_now()
    chunk_id = uuid4()

    doc_provider = FakeDocProvider([])

    vector_db = FakeVectorDb(
        [
            Chunk(
                id=chunk_id,
                content="",
                file_path="file1.txt",
                modified_at=now,
                line_end=10,
                line_start=4,
                raw_code=None,
                file_sha256_checksum="",
            )
        ]
    )

    dc = DeltaComputer(doc_provider, vector_db)
    to_delete, to_update, _ = dc.compute_deltas()

    assert to_delete == {chunk_id}
    assert to_update == set()


def test_detects_updated_document():
    now = utc_now()
    older = now - timedelta(days=1)
    chunk_id = uuid4()

    doc_provider = FakeDocProvider(
        [
            DocumentMeta(file_path="file1.txt", modified_at=now),
        ],
        content_by_path={"file1.txt": "updated content"},
    )

    vector_db = FakeVectorDb(
        [
            Chunk(
                id=chunk_id,
                content="",
                file_path="file1.txt",
                modified_at=older,
                line_start=1,
                line_end=10,
                raw_code=None,
                file_sha256_checksum="old_checksum",
            )
        ]
    )

    dc = DeltaComputer(doc_provider, vector_db, debounce_seconds=0)
    to_delete, to_update, _ = dc.compute_deltas()

    assert to_delete == {chunk_id}
    assert to_update == {"file1.txt"}
