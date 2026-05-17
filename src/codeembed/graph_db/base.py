from abc import ABC, abstractmethod
from typing import List, Optional, Set

from codeembed.graph_db.models import Edge, Subgraph


class GraphDbBase(ABC):
    # ------------------------
    # Traversal
    # ------------------------

    @abstractmethod
    def expand_nodes(
        self,
        node_ids: List[str],
        max_depth: int = 1,
        relations: Optional[Set[str]] = None,
    ) -> Subgraph:
        pass

    # ------------------------
    # Edge operations
    # ------------------------

    @abstractmethod
    def delete_node(self, node_id: str) -> None:
        pass

    @abstractmethod
    def add_edge(self, edge: Edge) -> None:
        pass

    @abstractmethod
    def delete_edges_by_file_path(self, file_path: str) -> None:
        pass

    @abstractmethod
    def delete_edge(
        self,
        source: str,
        target: str,
        relation: str,
    ) -> None:
        pass
