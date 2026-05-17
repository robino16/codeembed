from codeembed.doc_embedder.doc_embedder import _Edge, _normalize_edge


def test_relation_uppercased():
    edge = _Edge(source="A", relation="calls", target="B")
    assert _normalize_edge(edge).relation == "CALLS"


def test_relation_spaces_replaced_with_underscores():
    edge = _Edge(source="A", relation="is supplier of", target="B")
    assert _normalize_edge(edge).relation == "IS_SUPPLIER_OF"


def test_relation_mixed_case_and_spaces():
    edge = _Edge(source="A", relation="Is Supplier Of", target="B")
    assert _normalize_edge(edge).relation == "IS_SUPPLIER_OF"


def test_source_whitespace_stripped():
    edge = _Edge(source="  AuthService.login  ", relation="CALLS", target="B")
    assert _normalize_edge(edge).source == "AuthService.login"


def test_target_whitespace_stripped():
    edge = _Edge(source="A", relation="CALLS", target="  jwt_decode  ")
    assert _normalize_edge(edge).target == "jwt_decode"


def test_already_normalized_unchanged():
    edge = _Edge(source="AuthService.login", relation="CALLS", target="JwtService.sign")
    result = _normalize_edge(edge)
    assert result.source == "AuthService.login"
    assert result.relation == "CALLS"
    assert result.target == "JwtService.sign"
