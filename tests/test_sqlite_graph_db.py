from uuid import uuid4

from codeembed.graph_db.models import Edge
from codeembed.graph_db.sqlite_adapter import SqliteGraphDb


def _db() -> SqliteGraphDb:
    return SqliteGraphDb(":memory:")


def _edge(source: str, target: str, relation: str = "CALLS", file_path: str = "f.py") -> Edge:
    return Edge(source=source, target=target, relation=relation, file_path=file_path, chunk_id=uuid4())


def test_expand_nodes_empty_graph_returns_no_edges():
    db = _db()
    result = db.expand_nodes(["A"])
    assert result.edges == []


def test_expand_nodes_depth_1_returns_direct_neighbor():
    db = _db()
    db.add_edge(_edge("A", "B"))

    result = db.expand_nodes(["A"], max_depth=1)

    sources = {e.source for e in result.edges}
    targets = {e.target for e in result.edges}
    assert "A" in sources
    assert "B" in targets


def test_expand_nodes_depth_1_does_not_return_two_hop_neighbor():
    db = _db()
    db.add_edge(_edge("A", "B"))
    db.add_edge(_edge("B", "C"))

    result = db.expand_nodes(["A"], max_depth=1)

    targets = {e.target for e in result.edges}
    assert "C" not in targets


def test_expand_nodes_depth_2_returns_two_hop_neighbor():
    db = _db()
    db.add_edge(_edge("A", "B"))
    db.add_edge(_edge("B", "C"))

    result = db.expand_nodes(["A"], max_depth=2)

    targets = {e.target for e in result.edges}
    assert "B" in targets
    assert "C" in targets


def test_expand_nodes_depths_are_correct():
    db = _db()
    db.add_edge(_edge("A", "B"))
    db.add_edge(_edge("B", "C"))

    result = db.expand_nodes(["A"], max_depth=2)

    assert result.depths["A"] == 0
    assert result.depths["B"] == 1
    assert result.depths["C"] == 2


def test_expand_nodes_cycle_does_not_loop():
    db = _db()
    db.add_edge(_edge("A", "B"))
    db.add_edge(_edge("B", "A"))

    result = db.expand_nodes(["A"], max_depth=5)

    assert len(result.edges) == 2


def test_expand_nodes_relation_filter_excludes_other_relations():
    db = _db()
    db.add_edge(_edge("A", "B", relation="CALLS"))
    db.add_edge(_edge("A", "C", relation="IMPORTS"))

    result = db.expand_nodes(["A"], max_depth=1, relations={"CALLS"})

    targets = {e.target for e in result.edges}
    assert "B" in targets
    assert "C" not in targets


def test_expand_nodes_returns_chunk_id_on_edge():
    db = _db()
    chunk_id = uuid4()
    db.add_edge(Edge(source="A", target="B", relation="CALLS", file_path="f.py", chunk_id=chunk_id))

    result = db.expand_nodes(["A"], max_depth=1)

    assert len(result.edges) == 1
    assert result.edges[0].chunk_id == chunk_id


def test_delete_edges_by_file_path_removes_matching_edges():
    db = _db()
    db.add_edge(_edge("A", "B", file_path="auth.py"))
    db.add_edge(_edge("C", "D", file_path="utils.py"))

    db.delete_edges_by_file_path("auth.py")

    result = db.expand_nodes(["A"], max_depth=1)
    assert result.edges == []

    result = db.expand_nodes(["C"], max_depth=1)
    assert len(result.edges) == 1


def test_delete_edge_removes_specific_edge():
    db = _db()
    db.add_edge(_edge("A", "B", relation="CALLS"))
    db.add_edge(_edge("A", "C", relation="IMPORTS"))

    db.delete_edge("A", "B", "CALLS")

    result = db.expand_nodes(["A"], max_depth=1)
    targets = {e.target for e in result.edges}
    assert "B" not in targets
    assert "C" in targets


def test_add_edge_is_idempotent():
    db = _db()
    edge = _edge("A", "B")
    db.add_edge(edge)
    db.add_edge(edge)

    result = db.expand_nodes(["A"], max_depth=1)
    assert len(result.edges) == 1


def test_expand_nodes_multiple_starting_nodes():
    db = _db()
    db.add_edge(_edge("A", "C"))
    db.add_edge(_edge("B", "D"))

    result = db.expand_nodes(["A", "B"], max_depth=1)

    targets = {e.target for e in result.edges}
    assert "C" in targets
    assert "D" in targets
