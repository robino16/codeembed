from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Edge:
    source: str
    target: str
    relation: str
    file_path: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subgraph:
    edges: List[Edge] = field(default_factory=list)
    depths: Dict[str, int] = field(default_factory=dict)
