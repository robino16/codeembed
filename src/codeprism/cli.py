import os
import shutil
import subprocess

import typer

from codeprism.setup_logger import setup_logger

app = typer.Typer()

_CODEPRISM_DIR = ".codeprism"
_CONFIG_FILE = "codeprism.toml"
_GITIGNORE_ENTRY = ".codeprism/"
_DEFAULT_DEBOUNCE = 10
_DEFAULT_SLEEP_INTERVAL = 60

_CURATED_MODELS = [
    ("gpt-oss:20b", "OpenAI's open source model, ~14GB"),
    ("gemma4:e4b", "Google's all-around model, ~9.6GB"),
]


def _ensure_gitignore() -> None:
    if not os.path.isfile(".gitignore"):
        typer.echo("Error: No .gitignore found. Run 'codeprism init' from the root of your git repository.")
        typer.echo("A .gitignore is required to prevent CodePrism from embedding sensitive files.")
        raise typer.Exit(1)

    with open(".gitignore", "r", encoding="utf-8") as f:
        content = f.read()

    if _GITIGNORE_ENTRY not in content:
        with open(".gitignore", "a", encoding="utf-8") as f:
            f.write(f"\n# CodePrism\n{_GITIGNORE_ENTRY}\n")
        typer.echo(f"Added '{_GITIGNORE_ENTRY}' to .gitignore.")


def _create_codeprism_dir() -> None:
    if not os.path.isdir(_CODEPRISM_DIR):
        os.makedirs(_CODEPRISM_DIR)
        typer.echo(f"Created '{_CODEPRISM_DIR}/' directory.")


def _check_ollama_installed() -> None:
    if shutil.which("ollama") is None:
        typer.echo("Error: Ollama is not installed or not in your PATH.")
        typer.echo("Install it from https://ollama.com/ then re-run 'codeprism init'.")
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


def _select_model(downloaded_models: list[str]) -> str:
    typer.echo("\nSelect an LLM model for code summarization:\n")

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
        typer.echo("Invalid choice. Please re-run 'codeprism init'.")
        raise typer.Exit(1)

    if options[index] == "custom":
        return typer.prompt("Model name (e.g. gpt-oss:20b)")

    return options[index]


def _ensure_model_downloaded(model: str, downloaded_models: list[str]) -> None:
    if model in downloaded_models:
        return

    typer.echo(f"\nModel '{model}' is not downloaded yet.")
    if typer.confirm("Download it now?", default=False):
        typer.echo(f"Pulling '{model}'... (this may take a while)")
        subprocess.run(["ollama", "pull", model])
    else:
        typer.echo(f"Skipping. You can pull it later with: ollama pull {model}")


def _write_config(model: str) -> None:
    config_toml = f"""\
[codeprism]
llm_model = "{model}"
debounce = {_DEFAULT_DEBOUNCE}
sleep_interval = {_DEFAULT_SLEEP_INTERVAL}
"""
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(config_toml)

    typer.echo(f"Created '{_CONFIG_FILE}'.")


@app.command()
def init():
    """Initialize CodePrism in the current project."""
    typer.echo("Initializing CodePrism...\n")

    if os.path.isfile(_CONFIG_FILE):
        if not typer.confirm(f"'{_CONFIG_FILE}' already exists. Overwrite?", default=False):
            raise typer.Exit(0)

    _ensure_gitignore()
    _create_codeprism_dir()
    _check_ollama_installed()
    _check_ollama_running()

    downloaded_models = _get_downloaded_models()
    model = _select_model(downloaded_models)
    _ensure_model_downloaded(model, downloaded_models)
    _write_config(model)

    typer.echo("\nDone. Run 'codeprism serve' to start the MCP server.")


@app.command()
def serve():
    """Start the MCP server."""
    if not os.path.isfile(_CONFIG_FILE):
        typer.echo("Error: 'codeprism.toml' not found. Run 'codeprism init' first.")
        raise typer.Exit(1)

    setup_logger()
    _check_ollama_installed()
    _check_ollama_running()

    from codeprism.mcp_server import mcp
    typer.echo("Starting CodePrism MCP server...")
    mcp.run(transport="streamable-http")


@app.command()
def embed():
    """Embed codebase into the vector database."""
    if not os.path.isfile(_CONFIG_FILE):
        typer.echo("Error: 'codeprism.toml' not found. Run 'codeprism init' first.")
        raise typer.Exit(1)

    setup_logger()
    _check_ollama_installed()
    _check_ollama_running()

    typer.echo("Embedding codebase...\n")

    from codeprism.bootstrap.services import get_embedder_service
    embedder = get_embedder_service()
    embedder.embed_codebase()

    typer.echo("\nDone.")
