# CodePrism

This embeds your codebase and other codebases you need as context.

Uses [CromaDB](https://github.com/chroma-core/chroma) for quick and easy local vector storage.
Make sure you have installed [Python](python.org) and [uv](https://github.com/astral-sh/uv) (via `pip install uv`).

The codebase embedder works best in combination with LLM model for code analysis and summarization.
You can use local LLMs [Ollama](https://github.com/ollama/ollama-python).

The idea is that you do:

```bash
uv add codeprism
```

Then:

```bash
codeprism init
```

Just to make sure `.gitignore` excludes new folders.

The current codebase folder will automatically be embedded when running the MCP server.

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

The code embedder will apply the `.gitignore` in the root folder.
By default it also ignores: `node_modules/`, `venv/`, `.venv/`, `.env`, `.env.local`, `build/` and `dist/`.

## Contributing

### Running Tests

```bash
$env:PYTHONPATH="."
uv run pytest tests
```
