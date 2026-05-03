import logging

from bootstrap.services import get_search_service
from src.doc_search_service.doc_search_service import DocSearchService
from src.doc_embedder.doc_embedder import DocEmbedder
from src.doc_provider.local_doc_provider import LocalDocProvider
from src.llm.ollama_adapter import OllamaLLMService
from src.setup_logger import setup_logger
from src.vector_db.chromadb_adapter import ChromaDbAdapter

logger = logging.getLogger(__name__)


def main():
    setup_logger()

    logger.info("Starting codebase embedder...")

    doc_provider = LocalDocProvider(
        base_path=".",
        supported_file_extensions=["py"],
        skip_keywords=[
            "venv",
            "pytest_cache",
            "node_modules",
            ".env",
            "dist",
        ],  # consider using project's gitignore
    )
    vector_db = ChromaDbAdapter(collection_name="codebase")
    llm_service = OllamaLLMService()
    embedder = DocEmbedder(
        doc_provider, vector_db, llm_service, llm_model="gpt-oss:20b"
    )
    embedder.embed_codebase()

    search_query = "How does this code use LLMs?"
    search_service = get_search_service()
    search_result = search_service.search(search_query, top_n=5)

    print("Search result:")
    print(search_result)

    logger.info("Done!")


if __name__ == "__main__":
    main()
