# Codebase Embedder

This embeds your codebase and other codebases you need as context.

Uses [CromaDB](https://github.com/chroma-core/chroma) for quick and easy local vector storage.
Make sure you have installed [Python](python.org) and [uv](https://github.com/astral-sh/uv) (via `pip install uv`).

The codebase embedder works best in combination with LLM model for code analysis and summarization.
You can use local LLMs [Ollama](https://github.com/ollama/ollama-python).

The idea is that you do:

```bash
uv add <package-name>
```

Then:

```bash
<package-name> init
```

Just to make sure `.gitignore` excludes new folders.

The current codebase folder will automatically be embedded when running the MCP server.

You can then add extra codebases as context with:

```bash
<package-name> add <local-file-path>
```

or

```bash
<package-name> add <github-repo-url>
```

Then start the MCP server with:

```bash
<package-name> serve
```

## Contributing

### Running Tests

```bash
$env:PYTHONPATH="."
uv run pytest tests
```
