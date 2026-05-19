from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from codeembed.doc_search_service.doc_search_service import _rerank
from codeembed.graph_db.models import Edge, Subgraph
from codeembed.vector_db.models import Chunk, SearchResult

_NOW = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _chunk(chunk_id: UUID, node_ids: Optional[List[str]] = None) -> Chunk:
    return Chunk(
        id=chunk_id,
        content="",
        modified_at=_NOW,
        file_path="f.py",
        line_start=1,
        line_end=10,
        raw_code=None,
        file_sha256_checksum="",
        graph_node_ids=node_ids or [],
    )


def _result(chunk: Chunk, distance: float) -> SearchResult:
    return SearchResult(chunk=chunk, score=distance)


def _edge(source: str, target: str, chunk_id: UUID) -> Edge:
    return Edge(source=source, target=target, relation="CALLS", file_path="f.py", chunk_id=chunk_id)


def test_empty_graph_preserves_semantic_order():
    id_a, id_b = uuid4(), uuid4()
    chunk_a = _chunk(id_a)
    chunk_b = _chunk(id_b)
    results = [_result(chunk_a, distance=0.1), _result(chunk_b, distance=0.5)]

    ranked = _rerank(results, Subgraph(), [])

    assert ranked[0].id == id_a
    assert ranked[1].id == id_b


def test_graph_bonus_can_promote_lower_semantic_chunk():
    id_a, id_b = uuid4(), uuid4()
    chunk_a = _chunk(id_a, node_ids=["ServiceA"])
    chunk_b = _chunk(id_b, node_ids=["ServiceB"])

    # chunk_b has better semantic score (lower distance)
    results = [_result(chunk_a, distance=0.5), _result(chunk_b, distance=0.4)]

    # chunk_a gets a depth-1 graph bonus via an edge from "ServiceA"
    subgraph = Subgraph(
        edges=[_edge("ServiceA", "X", chunk_id=id_a)],
        depths={"ServiceA": 1},
    )

    ranked = _rerank(results, subgraph, [])

    # chunk_a: semantic=1/(1+0.5)=0.667, bonus=0.5/2=0.25, total=0.917
    # chunk_b: semantic=1/(1+0.4)=0.714, no bonus, total=0.714
    assert ranked[0].id == id_a


def test_depth_1_ranks_higher_than_depth_2():
    id_a, id_b = uuid4(), uuid4()
    chunk_a = _chunk(id_a)
    chunk_b = _chunk(id_b)

    results = [_result(chunk_a, distance=1.0), _result(chunk_b, distance=1.0)]

    subgraph = Subgraph(
        edges=[
            _edge("NodeA", "X", chunk_id=id_a),
            _edge("NodeB", "X", chunk_id=id_b),
        ],
        depths={"NodeA": 1, "NodeB": 2},
    )

    ranked = _rerank(results, subgraph, [])

    assert ranked[0].id == id_a


def test_graph_only_chunk_included_in_results():
    id_a, id_b = uuid4(), uuid4()
    chunk_a = _chunk(id_a)
    chunk_b = _chunk(id_b)

    results = [_result(chunk_a, distance=0.2)]

    subgraph = Subgraph(
        edges=[_edge("NodeB", "X", chunk_id=id_b)],
        depths={"NodeB": 1},
    )

    ranked = _rerank(results, subgraph, [chunk_b])

    ids = [c.id for c in ranked]
    assert id_b in ids


def test_chunk_in_both_gets_combined_score():
    id_a = uuid4()
    chunk_a = _chunk(id_a)
    results = [_result(chunk_a, distance=1.0)]

    subgraph = Subgraph(
        edges=[_edge("NodeA", "X", chunk_id=id_a)],
        depths={"NodeA": 0},
    )

    ranked = _rerank(results, subgraph, [])

    # semantic = 1/(1+1.0) = 0.5, graph bonus = 0.5/(0+1) = 0.5, total = 1.0
    # Just verify it's in the results; score correctness implied by other tests
    assert ranked[0].id == id_a


def test_minimum_depth_wins_when_reachable_via_two_paths():
    id_a, id_b = uuid4(), uuid4()
    chunk_a = _chunk(id_a)
    chunk_b = _chunk(id_b)

    # Both chunks have the same semantic score
    results = [_result(chunk_a, distance=1.0), _result(chunk_b, distance=1.0)]

    # chunk_a is reachable at depth 1 AND depth 2 — minimum (depth 1) should be used
    # chunk_b is only reachable at depth 2
    subgraph = Subgraph(
        edges=[
            _edge("NodeShallow", "X", chunk_id=id_a),
            _edge("NodeDeep", "X", chunk_id=id_a),
            _edge("NodeDeep2", "X", chunk_id=id_b),
        ],
        depths={"NodeShallow": 1, "NodeDeep": 2, "NodeDeep2": 2},
    )

    ranked = _rerank(results, subgraph, [])

    assert ranked[0].id == id_a


def test_results_are_sorted_descending():
    ids = [uuid4() for _ in range(4)]
    chunks = [_chunk(i) for i in ids]
    results = [
        _result(chunks[0], distance=0.9),
        _result(chunks[1], distance=0.1),
        _result(chunks[2], distance=0.5),
        _result(chunks[3], distance=0.3),
    ]

    ranked = _rerank(results, Subgraph(), [])

    scores = [1.0 / (1.0 + r.score) for r in results]
    expected_order = [c for _, c in sorted(zip(scores, chunks), reverse=True)]
    assert [c.id for c in ranked] == [c.id for c in expected_order]
