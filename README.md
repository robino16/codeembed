# codeembed

Embeds your codebase into a local vector database and exposes it as an MCP tool, giving AI assistants like Claude Code fast semantic search over your code.

Uses [ChromaDB](https://github.com/chroma-core/chroma) for local vector storage and [Ollama](https://github.com/ollama/ollama) for LLM analysis.

## Prerequisites

- [Python](https://python.org) 3.11+
- [uv](https://github.com/astral-sh/uv)
- [Ollama](https://ollama.com) running locally

## Installation

```bash
uv tool install codeembed
```

## Usage

**1. Initialize** (run once in your project root):

```bash
codeembed init
```

Creates a `codeembed.toml` config and adds `.codeembed/` to your `.gitignore`. You'll be prompted to select an Ollama model.

**2. Start the MCP server:**

```bash
codeembed serve
```

This embeds your codebase in the background and starts the MCP server. Respects `.gitignore`.

**3. Manually re-embed** (optional):

```bash
codeembed embed
```

## Add to Claude Code

```bash
claude mcp add codeembed -- uv run codeembed serve
```

Also add `mcp__codeembed__search` to `allowedTools` in your Claude config.

The MCP server exposes a single `search(query)` tool for semantic search over your codebase.

## Contributing

```bash
uv sync --extra dev
uv pip install -e .
claude mcp add codeembed -- uv run codeembed serve
```

Run tests:

```bash
uv run pytest tests
```
