import json
import logging
import sqlite3
from datetime import timezone
from typing import List, Optional, Tuple

from codeembed.doc_embedder.models import GraphAnalysisResultEdge
from codeembed.utils.checksum_utils import string_to_sha256
from codeembed.utils.time_utils import utc_now

logger = logging.getLogger(__name__)

_DB_PATH = ".codeembed/chunk_cache.db"


class ChunkCache:
    """SQLite-backed cache for LLM-generated segment summaries and graph edges.

    Keyed on sha256(segment content) so identical segments are never re-processed,
    even across files or runs.
    """

    def __init__(self, db_path: str = _DB_PATH) -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS chunk_cache (
                content_sha256   TEXT PRIMARY KEY,
                summary          TEXT NOT NULL,
                graph_edges_json TEXT NOT NULL,
                created_at       TEXT NOT NULL
            )
        """)
        self._conn.commit()

    def lookup(self, content: str) -> Optional[Tuple[str, List[GraphAnalysisResultEdge]]]:
        key = string_to_sha256(content)
        row = self._conn.execute(
            "SELECT summary, graph_edges_json FROM chunk_cache WHERE content_sha256 = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        summary, graph_edges_json = row
        edges = [GraphAnalysisResultEdge(**e) for e in json.loads(graph_edges_json)]
        return summary, edges

    def store(self, content: str, summary: str, edges: List[GraphAnalysisResultEdge]) -> None:
        key = string_to_sha256(content)
        self._conn.execute(
            "INSERT OR REPLACE INTO chunk_cache "
            "(content_sha256, summary, graph_edges_json, created_at) VALUES (?, ?, ?, ?)",
            (key, summary, json.dumps([e.model_dump() for e in edges]), utc_now().astimezone(timezone.utc).isoformat()),
        )
        self._conn.commit()
