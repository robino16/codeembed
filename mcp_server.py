from mcp.server.fastmcp import FastMCP

from bootstrap.services import get_search_service

mcp = FastMCP("Codebase Embedder", json_response=True)

search_service = get_search_service()


@mcp.tool()
def search(query: str, top_n: int = 10) -> str:
    """Searches the embedded codebases."""
    return search_service.search(query, top_n)


# NOTE: We could, e.g., add a tool to add codebases, but that sounds very risky.


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
