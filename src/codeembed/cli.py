import os
import shutil
import subprocess
from typing import Literal

import typer

from codeembed.bootstrap.services import get_config, get_llm_service
from codeembed.llm.base import LLMServiceBase
from codeembed.setup_logger import setup_logger

app = typer.Typer()

_CODEEMBED_DIR = ".codeembed"
_CONFIG_FILE = "codeembed.toml"
_GITIGNORE_ENTRY = ".codeembed/"
_DEFAULT_DEBOUNCE = 10
_DEFAULT_SLEEP_INTERVAL = 60

_CURATED_MODELS = [
    ("gpt-oss:20b", "OpenAI's open source model, ~14GB"),
    ("gemma4:e4b", "Google's all-around model, ~9.6GB"),
]

_OPENAI_CURATED_MODELS = [
    ("gpt-4.1-mini", "Lightweight and cost-effective"),
    ("gpt-5.4-mini", "Newer, lightweight and cost-effective"),
    ("gpt-5.4-nano", "Newer and super lightweight option"),
]


def _ensure_gitignore() -> None:
    if not os.path.isfile(".gitignore"):
        typer.echo("Error: No .gitignore found. Run 'codeembed init' from the root of your git repository.")
        typer.echo("A .gitignore is required to prevent CodeEmbed from embedding your sensitive files.")
        raise typer.Exit(1)

    with open(".gitignore", "r", encoding="utf-8") as f:
        content = f.read()

    if _GITIGNORE_ENTRY not in content:
        # ask user for permission to modify .gitignore
        typer.echo(f"CodeEmbed stores its data in the '{_CODEEMBED_DIR}/' directory.")
        typer.echo(f"You must add '{_GITIGNORE_ENTRY}' to your .gitignore to use CodeEmbed safely.")
        if not typer.confirm(f"Add '{_GITIGNORE_ENTRY}' to your .gitignore now?", default=True):
            typer.echo(f"Error: Gitignore is missing '{_GITIGNORE_ENTRY}' entry for safe operation.")
            raise typer.Exit(1)
        with open(".gitignore", "a", encoding="utf-8") as f:
            f.write(f"\n# CodeEmbed\n{_GITIGNORE_ENTRY}\n")
        typer.echo(f"Added '{_GITIGNORE_ENTRY}' to .gitignore. Remember to commit this change.\n")


def _create_codeembed_dir() -> None:
    if not os.path.isdir(_CODEEMBED_DIR):
        os.makedirs(_CODEEMBED_DIR)
        typer.echo(f"Created '{_CODEEMBED_DIR}/' directory.\n")


def _check_ollama_installed() -> None:
    if shutil.which("ollama") is None:
        typer.echo("Error: Ollama is not installed or not in your PATH.")
        typer.echo("Install it from https://ollama.com/ then re-run 'codeembed init'.")
        raise typer.Exit(1)


def _check_ollama_model_is_available(model: str) -> None:
    downloaded_models = _get_downloaded_models()
    if model not in downloaded_models:
        typer.echo(f"Error: Ollama model '{model}' is not available.")
        typer.echo(f"Download it with: ollama pull {model}")
        # Alternatively give option to download now.
        raise typer.Exit(1)


def _check_ollama_running() -> None:
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if result.returncode != 0:
        typer.echo("Error: Ollama server is not running.")
        typer.echo("Start it with: ollama serve")
        raise typer.Exit(1)


def _get_downloaded_models() -> list[str]:
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    lines = result.stdout.strip().splitlines()
    models = []
    for line in lines[1:]:  # skip header
        parts = line.split()
        if parts:
            models.append(parts[0])
    return models


def _select_ollama_llm_model(downloaded_models: list[str]) -> str:
    typer.echo("\nSelect a local LLM model for code summarization:\n")

    options: list[str] = []

    for model, description in _CURATED_MODELS:
        tag = " [downloaded]" if model in downloaded_models else ""
        options.append(model)
        typer.echo(f"  {len(options)}. {model} — {description}{tag}")

    extra = [m for m in downloaded_models if m not in dict(_CURATED_MODELS)]
    for model in extra:
        options.append(model)
        typer.echo(f"  {len(options)}. {model} [downloaded]")

    options.append("custom")
    typer.echo(f"  {len(options)}. Enter a custom model name\n")

    raw = typer.prompt(f"Choice (1-{len(options)})")

    try:
        index = int(raw) - 1
        if index < 0 or index >= len(options):
            raise ValueError()
    except ValueError:
        typer.echo("Invalid choice. Please re-run 'codeembed init'.")
        raise typer.Exit(1)

    if options[index] == "custom":
        return typer.prompt("Model name (e.g. gpt-oss:20b)")

    return options[index]


def _select_openai_model() -> str:
    typer.echo("\nSelect an OpenAI LLM deployment for code summarization:\n")

    options = list(_OPENAI_CURATED_MODELS)
    for i, (model, description) in enumerate(options, 1):
        typer.echo(f"  {i}. {model} — {description}")

    custom_index = len(options) + 1
    typer.echo(f"  {custom_index}. Enter a custom model name\n")

    raw = typer.prompt(f"Choice (1-{custom_index})")

    try:
        index = int(raw) - 1
        if index < 0 or index >= custom_index:
            raise ValueError()
    except ValueError:
        typer.echo("Invalid choice. Please re-run 'codeembed init'.")
        raise typer.Exit(1)

    if index == len(options):
        return typer.prompt("Model name (e.g. gpt-4o)")

    return options[index][0]


def _check_openai_credentials() -> str:
    if os.getenv("OPENAI_API_KEY"):
        return "[OPENAI_API_KEY set]"
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if azure_endpoint:
        if os.getenv("AZURE_OPENAI_API_KEY"):
            return "[Azure: endpoint + key set]"
        return "[Azure: endpoint set, using RBAC]"
    return "[no credentials found]"


def _select_provider() -> Literal["ollama", "openai"]:
    typer.echo("\nSelect an LLM provider for code summarization:\n")

    is_ollama_installed = shutil.which("ollama") is not None
    if is_ollama_installed:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        is_ollama_running = result.returncode == 0
    else:
        is_ollama_running = False

    ollama_status = "[running]" if is_ollama_running else "[not running]" if is_ollama_installed else "[not installed]"
    openai_status = _check_openai_credentials()

    typer.echo("  1. ollama " + ollama_status)
    typer.echo("  2. openai " + openai_status)

    raw = typer.prompt("Choice (1-2)")

    try:
        index = int(raw) - 1
        if index < 0 or index >= 2:
            raise ValueError()
    except ValueError:
        typer.echo("Invalid choice. Please re-run 'codeembed init'.")
        raise typer.Exit(1)

    if index == 0:
        return "ollama"
    elif index == 1:
        return "openai"
    raise ValueError("Invalid index")  # should never happen


def _ensure_model_downloaded(model: str, downloaded_models: list[str]) -> None:
    if model in downloaded_models:
        return

    typer.echo(f"\nModel '{model}' is not downloaded yet.")
    if typer.confirm("Download it now?", default=False):
        typer.echo(f"Pulling '{model}'... (this may take a while)")
        subprocess.run(["ollama", "pull", model])
    else:
        typer.echo(f"Skipping. You can pull it later with: ollama pull {model}")


def _write_config(model: str, provider: Literal["ollama", "openai"], env_var_path: str | None = None) -> None:
    config_toml = f"""\
[codeembed]
llm_model = "{model}"
provider = "{provider}"
debounce = {_DEFAULT_DEBOUNCE}
sleep_interval = {_DEFAULT_SLEEP_INTERVAL}
"""
    if env_var_path:
        config_toml += f'env_var_path = "{env_var_path}"\n'

    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(config_toml)

    typer.echo(f"Created '{_CONFIG_FILE}'.")


def _check_llm_is_available(llm_service: LLMServiceBase, llm_model: str) -> None:
    # Pings the LLM deployment. Raises exception if it's not available.
    try:
        llm_service.generate_response(
            [{"role": "system", "content": "Ping!"}],
            llm_model,
            temperature=0.0,
            max_tokens=1,
        )
    except Exception as e:
        typer.echo(f"Error: Failed to ping LLM model or deployment '{llm_model}'. Details: {e}")
        raise typer.Exit(1)


@app.command()
def init():
    """Initialize CodeEmbed in the current project."""
    typer.echo("Initializing CodeEmbed...\n")

    if os.path.isfile(_CONFIG_FILE):
        if not typer.confirm(f"'{_CONFIG_FILE}' already exists. Overwrite?", default=False):
            raise typer.Exit(0)

    env_var_path = typer.prompt(
        "Do you have a .env file path? (optional, press Enter to skip)", default="", show_default=False
    )
    if env_var_path:
        if not os.path.isfile(env_var_path):
            typer.echo(f"Error: File '{env_var_path}' not found.")
            raise typer.Exit(1)
        else:
            from dotenv import load_dotenv

            load_dotenv(env_var_path)

    _ensure_gitignore()
    _create_codeembed_dir()

    provider = _select_provider()

    if provider == "ollama":
        _check_ollama_installed()
        _check_ollama_running()
        downloaded_models = _get_downloaded_models()
        model = _select_ollama_llm_model(downloaded_models)
        _ensure_model_downloaded(model, downloaded_models)
    else:
        model = _select_openai_model()

    _write_config(model, provider, env_var_path)

    # TODO: Consider modifying .claude/settings.json to add our MCP server config.
    #       Just ask the user (add support for Claude Yes/No prompt).

    typer.echo("\nDone. Run 'codeembed serve' to start the MCP server.")


@app.command()
def serve():
    """Start the MCP server."""
    if not os.path.isfile(_CONFIG_FILE):
        typer.echo("Error: 'codeembed.toml' not found. Run 'codeembed init' first.")
        raise typer.Exit(1)

    config = get_config()

    if config.env_var_path:
        from dotenv import load_dotenv

        if not os.path.isfile(config.env_var_path):
            typer.echo(f"Error: Environment variable file '{config.env_var_path}' not found.")
            raise typer.Exit(1)
        load_dotenv(config.env_var_path)

    setup_logger()

    if config.provider == "ollama":
        _check_ollama_installed()
        _check_ollama_running()
        _check_ollama_model_is_available(config.llm_model)

    llm_service = get_llm_service()

    _check_llm_is_available(llm_service, config.llm_model)

    from codeembed.mcp_server import mcp

    typer.echo("Starting CodeEmbed MCP server...")
    mcp.run(transport="stdio")


@app.command()
def embed():
    """Embed codebase into the vector database."""
    if not os.path.isfile(_CONFIG_FILE):
        typer.echo("Error: 'codeembed.toml' not found. Run 'codeembed init' first.")
        raise typer.Exit(1)

    config = get_config()

    if config.env_var_path:
        from dotenv import load_dotenv

        if not os.path.isfile(config.env_var_path):
            typer.echo(f"Error: Environment variable file '{config.env_var_path}' not found.")
            raise typer.Exit(1)
        load_dotenv(config.env_var_path)

    setup_logger()

    if config.provider == "ollama":
        _check_ollama_installed()
        _check_ollama_running()
        _check_ollama_model_is_available(config.llm_model)

    llm_service = get_llm_service()

    _check_llm_is_available(llm_service, config.llm_model)

    typer.echo("Embedding codebase...\n")

    from codeembed.bootstrap.services import get_embedder_service

    embedder = get_embedder_service()
    embedder.embed_codebase()

    typer.echo("\nDone.")
