[![PyPI](https://img.shields.io/pypi/v/whoosh-reloaded.svg)](https://pypi.org/project/whoosh-reloaded/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/whoosh-reloaded.svg)](https://pypi.org/project/whoosh-reloaded/)
[![License](https://img.shields.io/pypi/l/whoosh-reloaded.svg)](https://pypi.org/project/whoosh-reloaded/)

# Whoosh-Reloaded

Whoosh-Reloaded is a pure-Python full-text indexing and search library. The 4.0 modernization targets Python 3.11+, modern packaging, strict quality gates, optional feature profiles, and automated semantic releases.

## Features

- Pure-Python full-text indexing and search.
- BM25/BM25F scoring.
- Fielded documents, query parsing, facets, highlighting, sorting, and spell checking.
- File-based storage with legacy-compatible imports.
- Optional profiles for models, async wrappers, vector search, embeddings, APIs, storage backends, watchers, fuzzy matching, phonetics, and metrics.

## Installation

```bash
pip install whoosh-reloaded
```

Development tooling:

```bash
pip install "whoosh-reloaded[dev]"
```

Optional profiles:

```bash
pip install "whoosh-reloaded[models,async]"
pip install "whoosh-reloaded[vector,embeddings]"
pip install "whoosh-reloaded[api,postgres,metrics]"
```

## Quality gates

The 4.0 quality policy requires every merged step to pass:

- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src/whoosh`
- `uv run pytest tests`
- `uv run python -m build`
- `uv run twine check dist/*`

CI validates these checks on Windows and Linux before merge.

## Development

```bash
uv python install 3.11
uv venv --python 3.11
uv sync --extra dev
```

## Contributing

Commits follow Conventional Commits so `python-semantic-release` can generate versions, changelogs, tags, GitHub releases, and PyPI publications from the `master` release branch.

Maintainers:

- [Sygil-Dev Organization](https://github.com/Sygil-Dev)
