import asyncio
from functools import lru_cache
import logging
import os

from config.models import CodebaseEmbedderConfig
from doc_embedder.doc_embedder import DocEmbedder
from doc_provider.local_doc_provider import LocalDocProvider
from llm.ollama_adapter import OllamaLLMService
from src.doc_search_service.doc_search_service import DocSearchService
from src.vector_db.chromadb_adapter import ChromaDbAdapter

logger = logging.getLogger(__name__)

_SUPPORTED_FILE_EXTENSIONS = ["py"]
_CONFIG_FILE_PATH = "codeprism_config.json"
_DEFAULT_LLM_MODEL = "gpt-oss:20b"
_DEFAULT_DEBOUNCE = 10


@lru_cache(maxsize=1)
def get_search_service() -> DocSearchService:
    vector_db = ChromaDbAdapter(collection_name="codebase_embeddings")
    search_service = DocSearchService(vector_db)
    return search_service


@lru_cache(maxsize=1)
def get_config() -> CodebaseEmbedderConfig:
    if os.path.isfile(_CONFIG_FILE_PATH):
        try:
            with open(_CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            return CodebaseEmbedderConfig.model_validate_json(content)
        except Exception:
            pass
    default_config = CodebaseEmbedderConfig(
        llm_model=_DEFAULT_LLM_MODEL,
        debounce=_DEFAULT_DEBOUNCE,
    )
    with open(_CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(default_config.model_dump_json(indent=2))
    return default_config


@lru_cache(maxsize=1)
def get_embedder_service() -> DocEmbedder:
    config = get_config()
    doc_provider = LocalDocProvider(
        base_path=".",
        supported_file_extensions=_SUPPORTED_FILE_EXTENSIONS,
        extra_skip_keywords=[],
    )
    vector_db = ChromaDbAdapter(collection_name="codebase")
    llm_service = OllamaLLMService()
    embedder = DocEmbedder(
        doc_provider,
        vector_db,
        llm_service,
        llm_model=config.llm_model,
        debounce_seconds=config.debounce
    )
    return embedder


async def embed_loop() -> None:
      embedder = get_embedder_service()
      while True:
          try:
              await asyncio.to_thread(embedder.embed_codebase)
          except Exception:
              logger.exception("Embedding run failed")
          await asyncio.sleep(60)
