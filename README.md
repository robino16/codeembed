# CodeEmbed

Embeds your codebase into a local vector database and exposes it as an MCP tool, giving AI assistants like Claude Code fast semantic search over your code.

Particularly useful for questions like:

- How is X implemented in this repo?
- Where is X defined or used?
- Does this repo already have X?

For other questions, the agent will fall back to normal lookups.
CodeEmbed can improve lookup speed and accuracy, especially for finding existing implementations before writing new ones.
Note that the biggest bottleneck in coding agents is LLM thinking and token generation — solid prompts and follow-up questions still matter.

Uses [ChromaDB](https://github.com/chroma-core/chroma) for local vector storage and either [Ollama](https://github.com/ollama/ollama) or OpenAI (including OpenAI models via Azure AI Foundry) for LLM analysis.

## Prerequisites

- [Python](https://python.org) 3.11+
- [uv](https://github.com/astral-sh/uv)
- One of:
  - [Ollama](https://ollama.com) running locally, **or**
  - An OpenAI API key or Azure OpenAI endpoint

## Installation

**With Ollama:**

```bash
uv tool install codeembed
```

**With OpenAI / Azure OpenAI:**

```bash
uv tool install 'codeembed[openai]'
```

> **Supply chain safety:** To reduce the risk of newly-published malicious packages, consider adding `exclude-newer = "7 days"` to your global [`uv.toml`](https://docs.astral.sh/uv/reference/settings/#exclude-newer). This prevents `uv` from installing packages published in the last 7 days.

### Manual installation (from source)

If CodeEmbed is not published to PyPI, install it directly from source:

```bash
git clone https://github.com/robino16/codeembed
cd codeembed

# With Ollama
uv tool install .

# With OpenAI support
uv tool install '.[openai]'
```

Then run `codeembed init` inside of your target repository.

## Upgrading

```bash
uv tool upgrade codeembed
```

## Usage

CodeEmbed is intended to be used within a single project — run all commands from your project root. Each project gets its own local vector database stored in `.codeembed/`.

Supported file types: `.py`, `.md`, `.ts`, `.tsx`, `.js`, `.jsx`.

**1. Initialize** (run once in your project root):

```bash
codeembed init
```

Creates a `codeembed.toml` config and configures your `.gitignore`. You'll be prompted to select a provider (Ollama or OpenAI) and a model. You'll also be offered the option to automatically configure Claude Code and/or GitHub Copilot.

**2. Pre-populate the index:**

```bash
codeembed embed
```

Run this before starting the server to pre-populate the index. Searches will return empty results until the first file has been embedded.

CodeEmbed respects your project's `.gitignore` and also excludes typical environment directories and files (`.env`, `venv`, `node_modules`, etc.) by default.

**3. Start the MCP server:**

```bash
codeembed serve
```

Starts the MCP server.
If the MCP server is added to Claude or GitHub Copilot, you do not need to do this.

The `serve` command will embed your codebase in the background - by default it will scan for changes every 60 seconds.

## Configuring OpenAI

If you use the OpenAI provider, credentials are read from environment variables. The recommended approach is a `.env` file. `codeembed init` will ask for the path, and it will be stored in `codeembed.toml` so `codeembed serve` and `codeembed embed` loads the `.env` file automatically.

### Standard OpenAI

```env
OPENAI_API_KEY=...
```

Optionally override the endpoint (for compatible APIs like vLLM, LM Studio, OpenRouter):

```env
OPENAI_API_KEY=...
OPENAI_BASE_URL=...
```

### Azure OpenAI — API key

```env
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=...
```

### Azure OpenAI — RBAC / Entra ID (keyless)

Set only the endpoint; CodeEmbed will use `DefaultAzureCredential`, which automatically tries multiple credential sources in order — service principals (via env vars), workload identity, managed identity, VS Code Azure sign-in, `az login`, Azure PowerShell, and `azd auth login` — falling back to an interactive browser window if none are found automatically:

```env
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/openai/v1/
```

## Add to Claude Code or GitHub Copilot

`codeembed init` will offer to configure these automatically. If you prefer to do it manually:

**Claude Code** — add to `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "codeembed": {
      "command": "codeembed",
      "args": ["serve"]
    }
  }
}
```

And add to `.claude/settings.local.json` to enable and pre-approve the tool:

```json
{
  "enabledMcpjsonServers": ["codeembed"],
  "permissions": {
    "allow": ["mcp__codeembed__search"]
  }
}
```

**GitHub Copilot** — add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "codeembed": {
      "command": "codeembed",
      "args": ["serve"]
    }
  }
}
```

The MCP server exposes a single `search(query)` tool for semantic search over your codebase.

## Contributing

Clone this repo with:

```bash
git@github.com:robino16/codeembed.git
```

```bash
cd codeembed
uv sync
```

Check for dependency conflicts with:

```bash
uv pip check
```

Check for package vulnerabilities with:

```bash
uv run pip-audit
```

(Optional) Add Ruff pre-commit with:

```bash
pre-commit install
```

Update init files:

```bash
uv run --no-sync scripts/generate_init_files.py
```

Run linter:

```bash
ruff check . --fix
```

Run formatter:

```bash
ruff format .
```

Run tests:

```bash
uv run --no-sync pytest
```

Build with:

```bash
uv build
```

Validate build with:

```bash
uv run twine check dist/*
```

> `--no-sync` is required for local dev commands when the MCP server is running, as uv holds a lock that blocks sync operations.
