from pathlib import Path

import pytest

from codeembed.doc_embedder.chunk_cache import ChunkCache
from codeembed.doc_embedder.models import GraphAnalysisResultEdge


@pytest.fixture
def cache(tmp_path: Path) -> ChunkCache:
    return ChunkCache(db_path=str(tmp_path / "cache.db"))


def test_lookup_miss(cache: ChunkCache) -> None:
    assert cache.lookup("some content") is None


def test_store_and_lookup_roundtrip(cache: ChunkCache) -> None:
    edges = [GraphAnalysisResultEdge(source="Foo.bar", relation="CALLS", target="baz")]
    cache.store("content", "a summary", edges)

    result = cache.lookup("content")
    assert result is not None
    summary, returned_edges = result
    assert summary == "a summary"
    assert len(returned_edges) == 1
    assert returned_edges[0].source == "Foo.bar"
    assert returned_edges[0].relation == "CALLS"
    assert returned_edges[0].target == "baz"


def test_cache_hit_same_content(cache: ChunkCache) -> None:
    cache.store("content", "summary", [])
    assert cache.lookup("content") is not None
    assert cache.lookup("content") is not None


def test_different_content_separate_entries(cache: ChunkCache) -> None:
    cache.store("content A", "summary A", [])
    cache.store("content B", "summary B", [])

    a = cache.lookup("content A")
    b = cache.lookup("content B")
    assert a is not None and a[0] == "summary A"
    assert b is not None and b[0] == "summary B"


def test_empty_edges(cache: ChunkCache) -> None:
    cache.store("content", "summary", [])
    result = cache.lookup("content")
    assert result is not None
    summary, edges = result
    assert summary == "summary"
    assert edges == []
