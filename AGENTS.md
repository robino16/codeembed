# Agent Instructions

## Python Coding Standards

Use `Union` (from `typing`) instead of `|`.
Use `Optional[<type>]` instead of `<type> | None`.
Strictly use type hints for all functions and methods.
Run tests with `uv run --no-sync pytest` (`--no-sync` flag is important).

## General

When asked for a PR review, do a simple git diff against the main branch.
Do not read PRs from GitHub. Do not use PR skill.
