import asyncio
import logging
import os
import tomllib
from functools import lru_cache

from codeembed.config.models import CodeEmbedConfig
from codeembed.doc_embedder.doc_embedder import DocEmbedder
from codeembed.doc_provider.local_doc_provider import LocalDocProvider
from codeembed.doc_search_service.doc_search_service import DocSearchService
from codeembed.llm.ollama_adapter import OllamaLLMService
from codeembed.vector_db.chromadb_adapter import ChromaDbAdapter

logger = logging.getLogger(__name__)

_SUPPORTED_FILE_EXTENSIONS = ["py"]
_CONFIG_FILE_PATH = "codeembed.toml"
_DEFAULT_LLM_MODEL = "gpt-oss:20b"
_DEFAULT_DEBOUNCE = 10
_DEFAULT_SLEEP_INTERVAL = 60


@lru_cache(maxsize=1)
def get_search_service() -> DocSearchService:
    vector_db = ChromaDbAdapter(collection_name="codebase")
    search_service = DocSearchService(vector_db)
    return search_service


@lru_cache(maxsize=1)
def get_config() -> CodeEmbedConfig:
    if os.path.isfile(_CONFIG_FILE_PATH):
        try:
            with open(_CONFIG_FILE_PATH, "rb") as f:
                data = tomllib.load(f)
            config = CodeEmbedConfig(**data["codeembed"])
            return config
        except Exception:
            pass
    default_config = CodeEmbedConfig(
        llm_model=_DEFAULT_LLM_MODEL,
        debounce=_DEFAULT_DEBOUNCE,
        sleep_interval=_DEFAULT_SLEEP_INTERVAL,
    )
    return default_config


@lru_cache(maxsize=1)
def get_embedder_service() -> DocEmbedder:
    config = get_config()
    doc_provider = LocalDocProvider(
        base_path=".",
        supported_file_extensions=_SUPPORTED_FILE_EXTENSIONS,
    )
    vector_db = ChromaDbAdapter(collection_name="codebase")
    llm_service = OllamaLLMService()
    embedder = DocEmbedder(
        doc_provider, vector_db, llm_service, llm_model=config.llm_model, debounce_seconds=config.debounce
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
