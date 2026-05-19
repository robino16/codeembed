import json
import sqlite3
from typing import List, Optional, Set
from uuid import UUID

from codeembed.graph_db.base import GraphDbBase
from codeembed.graph_db.models import Edge, Subgraph


class SqliteGraphDb(GraphDbBase):
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path)
        self._cur = self._conn.cursor()
        self._initialize_schema()

    # ------------------------
    # Traversal (GraphRAG core)
    # ------------------------

    def expand_nodes(
        self,
        node_ids: List[str],
        max_depth: int = 1,
        relations: Optional[Set[str]] = None,
    ) -> Subgraph:

        visited = set()
        frontier = set(node_ids)

        all_nodes = set(node_ids)
        depths = {n: 0 for n in node_ids}
        edges = []

        for depth in range(1, max_depth + 1):
            if not frontier:
                break

            placeholders = ",".join(["?"] * len(frontier))

            query = f"""
                SELECT source, target, relation, file_path, chunk_id, properties
                FROM edges
                WHERE source IN ({placeholders})
            """

            params = list(frontier)

            if relations:
                rel_placeholders = ",".join(["?"] * len(relations))
                query += f" AND relation IN ({rel_placeholders})"
                params += list(relations)

            self._cur.execute(query, params)
            rows = self._cur.fetchall()

            next_frontier = set()

            for src, tgt, rel, file_path, chunk_id, properties in rows:
                _properties = json.loads(properties) if properties else {}
                edges.append(
                    Edge(
                        source=src,
                        target=tgt,
                        relation=rel,
                        file_path=file_path,
                        chunk_id=UUID(chunk_id),
                        properties=_properties,
                    )
                )
                if tgt not in visited:
                    next_frontier.add(tgt)
                    depths[tgt] = depth

            visited |= frontier
            frontier = next_frontier
            all_nodes |= next_frontier

        return Subgraph(edges=edges, depths=depths)

    # ------------------------
    # Edge operations
    # ------------------------

    def add_edge(self, edge: Edge) -> None:
        self.add_edges([edge])

    def add_edges(self, edges: List[Edge]) -> None:
        self._cur.executemany(
            "INSERT OR REPLACE INTO edges (source, target, relation, file_path, chunk_id, properties) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [(e.source, e.target, e.relation, e.file_path, str(e.chunk_id), json.dumps(e.properties)) for e in edges],
        )
        self._conn.commit()

    def delete_edge(self, source: str, target: str, relation: str) -> None:
        self._cur.execute(
            "DELETE FROM edges WHERE source = ? AND target = ? AND relation = ?",
            (source, target, relation),
        )
        self._conn.commit()

    def delete_edges_by_file_path(self, file_path: str) -> None:
        self._cur.execute(
            "DELETE FROM edges WHERE file_path = ?",
            (file_path,),
        )
        self._conn.commit()

    # ------------------------
    # Schema
    # ------------------------

    def _initialize_schema(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                source TEXT,
                target TEXT,
                relation TEXT,
                file_path TEXT,
                chunk_id TEXT,
                properties TEXT,
                PRIMARY KEY (source, target, relation)
            )
        """)

        self._conn.commit()
