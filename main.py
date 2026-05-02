import logging

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
        supported_extensions=["py"],
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

    logger.info("Done!")


if __name__ == "__main__":
    main()
