# Changelog

## Unreleased

### Added

- Added initial GraphRAG implementation.
- Added support for OpenCode in `init` cli command.
- Added option to start embedding at the end of `init` cli command.
- Added cross-process file locking to prevent multiple CodeEmbed instances from processing the same file simultaneously.
- Added chunk-level LLM result cache: summaries and graph relations are reused for unchanged code segments, avoiding redundant LLM calls when only part of a file changes.

### Changed

- Embed loop now rechecks for new changes immediately after processing files instead of sleeping unconditionally, reducing latency between a file change and it being embedded.

## 0.1.1

- Fix issue with module not found error for `openai` when using Ollama only.

## 0.1.0

Initial version.
