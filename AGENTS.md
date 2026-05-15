# Agent Instructions

## Python Coding Standards

- Use `Union` (from `typing`) instead of `|`.
- Use `Optional[<type>]` instead of `<type> | None`.
- Strictly use type hints for all functions and methods.
- Run tests with `uv run --no-sync pytest` (`--no-sync` flag is important).

## General

When asked for a PR review, do a simple git diff against the main branch.
Do not read PRs from GitHub.
Do not use PR skill.

## Codebase search

Use the `mcp__codeembed__search` tool as the first step for any question about how this codebase works — how something is implemented, where something is defined, what calls what. Prefer it over grep or file reads for exploratory questions.
