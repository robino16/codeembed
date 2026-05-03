import asyncio
from contextlib import asynccontextmanager, suppress

from mcp.server.fastmcp import FastMCP

from src.bootstrap.services import embed_loop, get_search_service


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

search_service = get_search_service()


@mcp.tool()
def search(query: str, top_n: int = 10) -> str:
    """Searches the embedded codebases."""
    return search_service.search(query, top_n)


# NOTE: We could, e.g., add a tool to add codebases, but that sounds very risky.


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
