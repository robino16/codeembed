import asyncio
import logging
import os
import tomllib
from functools import lru_cache

from codeembed.config.models import CodeEmbedConfig
from codeembed.cost_tracking.llm_wrapper import LLMServiceWithCostTracking
from codeembed.cost_tracking.models import Session
from codeembed.doc_embedder.doc_embedder import DocEmbedder
from codeembed.doc_provider.local_doc_provider import LocalDocProvider
from codeembed.doc_search_service.doc_search_service import DocSearchService
from codeembed.graph_db.sqlite_adapter import SqliteGraphDb
from codeembed.llm.base import LLMServiceBase
from codeembed.llm.ollama_adapter import OllamaLLMService
from codeembed.vector_db.chromadb_adapter import ChromaDbAdapter

logger = logging.getLogger(__name__)

_SUPPORTED_FILE_EXTENSIONS = ["py", "md", "ts", "tsx", "js", "jsx"]
_CONFIG_FILE_PATH = "codeembed.toml"
_DEFAULT_LLM_MODEL = "gpt-oss:20b"
_DEFAULT_DEBOUNCE = 10
_DEFAULT_SLEEP_INTERVAL = 60


@lru_cache(maxsize=1)
def get_vector_db() -> ChromaDbAdapter:
    return ChromaDbAdapter(collection_name="codebase")


@lru_cache(maxsize=1)
def get_graph_db() -> SqliteGraphDb:
    return SqliteGraphDb(db_path=".codeembed/graph.db")


@lru_cache(maxsize=1)
def get_search_service() -> DocSearchService:
    vector_db = get_vector_db()
    graph_db = get_graph_db()
    search_service = DocSearchService(vector_db, graph_db)
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


def _get_llm_service() -> LLMServiceBase:
    config = get_config()

    #
    # Ollama
    #
    if config.provider == "ollama":
        return OllamaLLMService()

    #
    # OpenAI-compatible providers
    #
    if config.provider != "openai":
        raise ValueError(f"Unsupported LLM provider: {config.provider}")

    try:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        from openai import OpenAI

        from codeembed.llm.openai_adapter import OpenAILLMService
    except ImportError as e:
        raise ImportError(
            "OpenAI provider requires optional dependencies. Install them with:\n  uv tool install 'codeembed[openai]'"
        ) from e

    #
    # Explicit config env-var overrides
    #
    custom_endpoint = os.getenv(config.llm_api_endpoint_env_var) if config.llm_api_endpoint_env_var else None

    custom_api_key = os.getenv(config.llm_api_key_env_var) if config.llm_api_key_env_var else None

    #
    # Generic OpenAI-compatible configuration
    #
    openai_api_key = custom_api_key or os.getenv("OPENAI_API_KEY")

    openai_base_url = custom_endpoint or os.getenv("OPENAI_BASE_URL")

    #
    # Azure OpenAI configuration
    #
    azure_openai_endpoint = custom_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")

    azure_openai_api_key = custom_api_key or os.getenv("AZURE_OPENAI_API_KEY")

    #
    # ----------------------------------------------------------
    # Standard OpenAI or OpenAI-compatible endpoint
    #
    # Examples:
    # - OpenAI cloud
    # - vLLM
    # - LM Studio
    # - Ollama OpenAI shim
    # - OpenRouter
    # - local gateways
    # ----------------------------------------------------------
    #
    if openai_api_key:
        client = OpenAI(
            api_key=openai_api_key,
            base_url=openai_base_url,
        )

        return OpenAILLMService(client)

    #
    # ----------------------------------------------------------
    # Azure OpenAI with API key
    # ----------------------------------------------------------
    #
    if azure_openai_endpoint and azure_openai_api_key:
        client = OpenAI(
            base_url=azure_openai_endpoint,
            api_key=azure_openai_api_key,
        )

        return OpenAILLMService(client)

    #
    # ----------------------------------------------------------
    # Azure OpenAI with RBAC / Entra ID
    #
    # DefaultAzureCredential tries these in order:
    # - Environment / service principal (AZURE_CLIENT_ID etc.)
    # - Workload Identity
    # - Managed Identity
    # - VS Code Azure sign-in
    # - Azure CLI (az login)
    # - Azure PowerShell (Connect-AzAccount)
    # - Azure Developer CLI (azd auth login)
    # - Interactive browser (last resort; enabled via exclude_interactive_browser_credential=False)
    # ----------------------------------------------------------
    #
    if azure_openai_endpoint:
        # expected format: https://<resource-name>.openai.azure.com/openai/v1/
        if not azure_openai_endpoint.startswith("https://") or ".openai.azure.com" not in azure_openai_endpoint:
            raise ValueError(f"Invalid Azure OpenAI endpoint: {azure_openai_endpoint}")
        elif not azure_openai_endpoint.endswith("/openai/v1/"):
            logger.warning(f"Azure OpenAI endpoint {azure_openai_endpoint} does not end with the expected /openai/v1/.")

        credential = DefaultAzureCredential(
            exclude_interactive_browser_credential=False,
        )

        token_provider = get_bearer_token_provider(
            credential,
            "https://cognitiveservices.azure.com/.default",
        )

        client = OpenAI(
            base_url=azure_openai_endpoint,
            api_key=token_provider,
        )

        return OpenAILLMService(client)

    raise ValueError(
        "Unable to configure OpenAI client.\n"
        "Expected one of:\n"
        "- OPENAI_API_KEY\n"
        "- AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT\n"
        "- AZURE_OPENAI_ENDPOINT with RBAC-enabled identity"
    )


@lru_cache(maxsize=1)
def get_session() -> Session:
    return Session()


@lru_cache(maxsize=1)
def get_llm_service() -> LLMServiceBase:
    session = get_session()
    llm_service = _get_llm_service()
    llm_service = LLMServiceWithCostTracking(llm_service, session)
    return llm_service


@lru_cache(maxsize=1)
def get_embedder_service() -> DocEmbedder:
    config = get_config()
    doc_provider = LocalDocProvider(
        base_path=".",
        supported_file_extensions=_SUPPORTED_FILE_EXTENSIONS,
    )
    vector_db = get_vector_db()
    llm_service = get_llm_service()
    graph_db = get_graph_db()
    embedder = DocEmbedder(
        doc_provider, vector_db, graph_db, llm_service, llm_model=config.llm_model, debounce_seconds=config.debounce
    )
    return embedder


async def embed_loop() -> None:
    embedder = get_embedder_service()
    session = get_session()
    config = get_config()
    while True:
        try:
            await asyncio.to_thread(embedder.embed_codebase)
        except Exception:
            logger.exception("Embedding run failed")
        session.save()
        logger.info(
            f"Input tokens used: {session.input_tokens}, output tokens used: {session.output_tokens}."
            f"Sleeping for {config.sleep_interval} seconds..."
        )
        await asyncio.sleep(config.sleep_interval)
