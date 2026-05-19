from typing import Dict, List

from codeembed.graph_db.base import GraphDbBase
from codeembed.graph_db.models import Subgraph
from codeembed.utils.string_utils import truncate_string
from codeembed.vector_db.base import VectorDbBase
from codeembed.vector_db.models import Chunk, SearchResult

_GRAPH_WEIGHT = 0.5


def _rerank(
    search_results: List[SearchResult],
    graph_results: Subgraph,
    graph_chunks: List[Chunk],
) -> List[Chunk]:
    chunk_id_to_depth: Dict[str, int] = {}
    for edge in graph_results.edges:
        depth = graph_results.depths.get(edge.source)
        if depth is None:
            continue
        chunk_id = str(edge.chunk_id)
        if chunk_id not in chunk_id_to_depth or depth < chunk_id_to_depth[chunk_id]:
            chunk_id_to_depth[chunk_id] = depth

    score_by_chunk_id: Dict[str, float] = {}
    for r in search_results:
        score_by_chunk_id[str(r.chunk.id)] = 1.0 / (1.0 + r.score)
    for chunk_id, depth in chunk_id_to_depth.items():
        score_by_chunk_id[chunk_id] = score_by_chunk_id.get(chunk_id, 0.0) + _GRAPH_WEIGHT / (depth + 1)

    all_chunks: Dict[str, Chunk] = {str(r.chunk.id): r.chunk for r in search_results}
    all_chunks.update({str(c.id): c for c in graph_chunks})
    return sorted(all_chunks.values(), key=lambda c: score_by_chunk_id.get(str(c.id), 0.0), reverse=True)


class DocSearchService:
    """
    The service that searches for relevant content from vector database and formats it for LLM consumption.
    """

    def __init__(
        self,
        vector_db: VectorDbBase,
        graph_db: GraphDbBase,
    ) -> None:
        self._vector_db = vector_db
        self._graph_db = graph_db

    def search(self, query: str, top_n: int = 10) -> str:
        """Searches for relevant content from vector database and formats it for LLM consumption."""

        # Initial vector search using semantic similarity (vector embedding).
        search_results = self._vector_db.search(query, top_n)

        # Get initial graph relations
        node_ids = list(set(node_id for result in search_results for node_id in result.chunk.graph_node_ids))

        # Expand with GraphRAG (graph traversal) to get nearby chunks.
        graph_results = self._graph_db.expand_nodes(node_ids, max_depth=2)

        # Fetch chunks for the graph results.
        initial_chunk_ids = list(set(result.chunk.id for result in search_results))
        graph_chunk_ids = list(
            set(edge.chunk_id for edge in graph_results.edges if edge.chunk_id not in initial_chunk_ids)
        )
        graph_chunks = self._vector_db.get_chunks(graph_chunk_ids)

        ranked_chunks = _rerank(search_results, graph_results, graph_chunks)

        # Collect all node IDs represented in ranked chunks for edge filtering.
        ranked_node_ids = set(node_id for chunk in ranked_chunks for node_id in chunk.graph_node_ids)

        # Keep only edges where both endpoints are visible in context. Deduplicate by (source, relation, target).
        seen_edges: set = set()
        visible_edges = []
        for edge in graph_results.edges:
            key = (edge.source, edge.relation, edge.target)
            if key in seen_edges:
                continue
            if edge.source in ranked_node_ids and edge.target in ranked_node_ids:
                seen_edges.add(key)
                visible_edges.append(edge)

        chunks_by_file: Dict[str, List[Chunk]] = {}
        for chunk in ranked_chunks:
            if chunk.file_path not in chunks_by_file:
                chunks_by_file[chunk.file_path] = []
            chunks_by_file[chunk.file_path].append(chunk)

        res = f"<SearchQuery>{query}</SearchQuery>\n"
        res += f"<TopN>{top_n}</TopN>\n"
        res += f"<Results chunkCount={len(ranked_chunks)} fileCount={len(chunks_by_file)}>\n"
        for file_path, chunks in chunks_by_file.items():
            res += f'  <File path="{file_path}">\n'
            for chunk in chunks:
                # NOTE: Consider truncating by number of tokens.
                raw_code = chunk.raw_code if chunk.raw_code else ""
                res += "    <Chunk>\n"
                res += f"      <Summary>\n{truncate_string(chunk.content, 4096)}\n      </Summary>\n"
                res += (
                    f'      <RawCode lines="{chunk.line_start}-{chunk.line_end}">\n'
                    f"{truncate_string(raw_code, 4096)}\n"
                    f"      </RawCode>\n"
                )
                res += "    </Chunk>\n"
            res += "  </File>\n"
        if visible_edges:
            res += "  <GraphRelations>\n"
            for edge in visible_edges:
                res += f'    <Edge source="{edge.source}" relation="{edge.relation}" target="{edge.target}" />\n'
            res += "  </GraphRelations>\n"
        res += "</Results>\n"
        return res
