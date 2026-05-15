import asyncio
from contextlib import asynccontextmanager, suppress

from mcp.server.fastmcp import FastMCP

from codeembed.bootstrap.services import embed_loop, get_search_service


@asynccontextmanager
async def lifespan(server):
    task = asyncio.create_task(embed_loop())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


mcp = FastMCP("Codebase Embedder", lifespan=lifespan, json_response=True)


@mcp.tool()
def search(query: str, top_n: int = 10) -> str:
    """Searches the embedded codebases using semantic similarity.

    Use this tool as the FIRST step for any question about the codebase — how something
    works, where something is defined, what calls what, etc. Prefer this over grep or
    file reads for exploratory questions; it returns ranked, summarized results instantly.

    Args:
        query: A natural-language description of what you're looking for.
               Examples: "how are deltas computed", "LLM service abstraction",
               "error handling in the embedding pipeline".
        top_n: Number of results to return (default 10).
    """
    search_service = get_search_service()
    return search_service.search(query, top_n)


# NOTE: We could, e.g., add a tool to add codebases, but that sounds very risky.


if __name__ == "__main__":
    mcp.run(transport="stdio")
