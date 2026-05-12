import asyncio
import logging
import os
import tomllib
from functools import lru_cache

from azure.identity import (
    DefaultAzureCredential,
    get_bearer_token_provider,
)
from openai import AzureOpenAI

from codeembed.config.models import CodeEmbedConfig
from codeembed.doc_embedder.doc_embedder import DocEmbedder
from codeembed.doc_provider.local_doc_provider import LocalDocProvider
from codeembed.doc_search_service.doc_search_service import DocSearchService
from codeembed.llm.base import LLMServiceBase
from codeembed.llm.ollama_adapter import OllamaLLMService
from codeembed.llm.openai_adapter import OpenAILLMService
from codeembed.vector_db.chromadb_adapter import ChromaDbAdapter

logger = logging.getLogger(__name__)

_SUPPORTED_FILE_EXTENSIONS = ["py"]
_CONFIG_FILE_PATH = "codeembed.toml"
_DEFAULT_LLM_MODEL = "gpt-oss:20b"
_DEFAULT_DEBOUNCE = 10
_DEFAULT_SLEEP_INTERVAL = 60
_DEFAULT_OPENAI_API_VERSION = "2024-10-21"  # TODO: Verify that this is a valid and working API version.


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
def get_llm_service() -> LLMServiceBase:
    config = get_config()
    if config.provider == "ollama":
        return OllamaLLMService()
    elif config.provider == "openai":
        from openai import OpenAI

        endpoint = config.llm_endpoint or None

        api_key = os.getenv(config.llm_api_key_env_var) if config.llm_api_key_env_var else os.getenv("OPENAI_API_KEY")

        # Standard OpenAI API key flow
        if api_key and not endpoint:
            client = OpenAI()
            return OpenAILLMService(client)

        # Azure OpenAI with API key
        if endpoint and api_key:
            client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=_DEFAULT_OPENAI_API_VERSION,
            )

            return OpenAILLMService(client)

        if not endpoint:
            raise ValueError("Unable to configure OpenAI client. Provide API key or Azure endpoint.")

        # Azure OpenAI with RBAC / Entra ID
        # User should have done `az login` in a terminal for easier auth experience.
        credential = DefaultAzureCredential(
            exclude_interactive_browser_credential=False,
        )

        token_provider = get_bearer_token_provider(
            credential,
            "https://cognitiveservices.azure.com/.default",
        )

        client = AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=token_provider,
            api_version=_DEFAULT_OPENAI_API_VERSION,
        )

        return OpenAILLMService(client)
    else:
        raise ValueError(f"Unsupported LLM provider: {config.provider}")


@lru_cache(maxsize=1)
def get_embedder_service() -> DocEmbedder:
    config = get_config()
    doc_provider = LocalDocProvider(
        base_path=".",
        supported_file_extensions=_SUPPORTED_FILE_EXTENSIONS,
    )
    vector_db = ChromaDbAdapter(collection_name="codebase")
    llm_service = get_llm_service()
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
