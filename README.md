# CodeEmbed

Embeds your codebase into a local vector database and exposes it as an MCP tool, giving AI assistants like Claude Code fast semantic search over your code.

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

## Usage

CodeEmbed is intended to be used within a single project — run all commands from your project root. Each project gets its own local vector database stored in `.codeembed/`.

**1. Initialize** (run once in your project root):

```bash
codeembed init
```

Creates a `codeembed.toml` config and configures your `.gitignore`. You'll be prompted to select a provider (Ollama or OpenAI) and a model. You'll also be offered the option to automatically configure Claude Code and/or GitHub Copilot.

**2. Pre-populate the index:**

```bash
codeembed embed
```

Run this before starting the server — searches return nothing until at least one embed run completes.

**3. Start the MCP server:**

```bash
codeembed serve
```

Starts the MCP server. Respects your `.gitignore`.

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

Set only the endpoint; CodeEmbed will use `DefaultAzureCredential` (supports `az login`, managed identity, VS Code Azure sign-in, workload identity federation, and service principals):

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

```bash
uv sync
uv pip install -e .
claude mcp add codeembed -- uv run codeembed serve
```

Optionally add Ruff pre-commit with:

```bash
pre-commit install
```

Run tests:

```bash
uv run pytest tests
```
