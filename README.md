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

## Usage

**1. Initialize** (run once in your project root):

```bash
codeembed init
```

Creates a `codeembed.toml` config and configures your `.gitignore`. You'll be prompted to select a provider (Ollama or OpenAI) and a model.

**2. Start the MCP server:**

```bash
codeembed serve
```

This embeds your codebase in the background and starts the MCP server. Respects your `.gitignore`.

**3. Manually re-embed** (optional):

```bash
codeembed embed
```

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

## Add to Claude Code

```bash
claude mcp add codeembed -- uv run codeembed serve
```

Also add `mcp__codeembed__search` to `allowedTools` in your Claude config.

The MCP server exposes a single `search(query)` tool for semantic search over your codebase.

It appears you need to run:

```bash
codeembed serve
claude
```

in order to make this work? Which makes little sense.

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
