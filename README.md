# CodePrism

This embeds your codebase and other codebases you need as context.

Uses [CromaDB](https://github.com/chroma-core/chroma) for quick and easy local vector storage.
Make sure you have installed [Python](python.org) and [uv](https://github.com/astral-sh/uv) (via `pip install uv`).

The codebase embedder works best in combination with LLM model for code analysis and summarization.
You can use local LLMs [Ollama](https://github.com/ollama/ollama-python).

The idea is that you do:

```bash
uv tool install codeprism
```

Then:

```bash
codeprism init
```

The current codebase folder will automatically be embedded when running the MCP server.

**NOT IMPLEMENTED YET**

You can then add extra codebases as context with:

```bash
codeprism add <local-file-path>
```

or

```bash
codeprism add <github-repo-url>
```

Then start the MCP server with:

```bash
codeprism serve
```

This will automatically embed your codebase in the background using Ollama.

You can also manually embed the codebase with:

```bash
codeprism embed
```

The code embedder will apply the `.gitignore` in the root folder.

## Add to Claude Code

```bash
claude mcp add codeprism -- uv run codeprism serve
```

Also add `mcp__codeprism__search` to `allowedTools` in Claude's config file.

## Contributing

### Setup

Install the package in editable mode so imports resolve correctly:

```bash
uv pip install -e .
```

### Running Tests

```bash
uv run pytest tests
```
