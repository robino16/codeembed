import os
import shutil
import subprocess

import typer

from setup_logger import setup_logger

app = typer.Typer()

@app.command()
def init():
    """Initialize CodePrism in the current project."""

    logger = setup_logger()

    # We make sure ./codeprism/ is ignored in .gitignore
    if not os.path.isfile(".gitignore"):
        raise FileNotFoundError("No .gitignore found. Please run this command in the root of your git repository. A .gitignore file is crucial to ensure CodePrism don't embed sensitive files.")
    with open(".gitignore", "r", encoding="utf-8") as f:
        gitignore_content = f.read()
    if "codeprism/" not in gitignore_content:
        logger.info("Adding 'codeprism/' to .gitignore...")
        with open(".gitignore", "a", encoding="utf-8") as f:
            f.write("\n# CodePrism\ncodeprism/\n")

    ollama = shutil.which("ollama")
    if ollama is None:
        raise EnvironmentError("Ollama CLI not found. Please install Ollama from https://ollama.com/ and make sure it's in your PATH.")

    llm_models = subprocess.run(["ollama", "list"], capture_output=True, text=True)


@app.command()
def serve():
    """Start the MCP server."""
    ...
