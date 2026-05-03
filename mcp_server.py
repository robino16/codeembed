from mcp.server.fastmcp import FastMCP

from doc_search_service.doc_search_service import DocSearchService
from vector_db.chromadb_adapter import ChromaDbAdapter

mcp = FastMCP("Codebase Embedder", json_response=True)

# NOTE: Consider moving these to src/bootstrap/ or similar.
vector_db = ChromaDbAdapter(collection_name="codebase_embeddings")

search_service = DocSearchService(vector_db)


@mcp.tool()
def search(query: str, top_n: int = 10) -> str:
    """Searches the embedded codebases."""
    return search_service.search(query, top_n)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
