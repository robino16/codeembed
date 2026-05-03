from utils.string_utils import truncate_string
from vector_db.base import VectorDbBase


class DocSearchService:
    """
    The service that searches for relevant content from vector database and formats it for LLM consumption.
    """

    def __init__(
        self,
        vector_db: VectorDbBase,
    ) -> None:
        self._vector_db = vector_db

    def search(self, query: str, top_n: int = 10) -> str:
        """Searches for relevant content from vector database and formats it for LLM consumption."""
        chunks = self._vector_db.search(query, top_n)

        chunks_by_file = {}

        for chunk in chunks:
            if chunk.file_path not in chunks_by_file:
                chunks_by_file[chunk.file_path] = []
            chunks_by_file[chunk.file_path].append(chunk)

        res = f"<SearchQuery>{query}</SearchQuery>\n"
        res += f"<TopN>{top_n}</TopN>\n"
        res += f"<Results chunkCount={len(chunks)} fileCount={len(chunks_by_file)}>\n"
        for file_path, chunks in chunks_by_file.items():
            res += f"  <File path=\"{file_path}\">\n"
            for chunk in chunks:
                # NOTE: Consider truncating by number of tokens.
                raw_code = chunk.raw_code if chunk.raw_code else ""
                res += f"    <Chunk lines=\"{chunk.start}-{chunk.end}\">\n"
                res += f"      <Summary>\n{truncate_string(chunk.content, 1024)}\n      </Summary>\n"
                res += f"      <RawCode>\n{truncate_string(raw_code, 1024)}\n      </RawCode>\n"
                res += "    </Chunk>\n"
            res += "  </File>\n"
        res += "</Results>\n"
        return res
