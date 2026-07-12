[![PyPI](https://img.shields.io/pypi/v/whoosh-ng.svg)](https://pypi.org/project/whoosh-ng/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/whoosh-ng.svg)](https://pypi.org/project/whoosh-ng/)
[![License](https://img.shields.io/pypi/l/whoosh-ng.svg)](https://pypi.org/project/whoosh-ng/)
[![Documentation](https://img.shields.io/badge/docs-yes-blue.svg)](https://dorel14.github.io/Whoosh-NG/)

# Whoosh-NG

**Whoosh-Reloaded** is a modern, pure-Python full-text indexing and search library. Version 4.0 brings a complete modernization with Python 3.11+ support, strict type annotations, optional feature profiles, and automated semantic releases.

## Quick Start

```bash
pip install whoosh-ng
```

## Features

- **Pure Python** - No native dependencies, works everywhere Python runs
- **Full-text search** - BM25/BM25F scoring with phrase queries
- **Fielded documents** - Structured indexing with typed fields
- **Query parsing** - Flexible parser with boosting and syntax options
- **Facets & sorting** - Group and sort results by any field
- **Highlighting** - Snippet extraction with customizable formatters
- **Spell checking** - Built-in spelling correction
- **Event-driven architecture** - Plugin system with hooks and middleware
- **Optional extensions** - Vector search, async, FastAPI, metrics, and more

## Installation

### Core Installation

```bash
pip install whoosh-ng
```

### Optional Profiles

```bash
# Vector search with NumPy
pip install "whoosh-ng[vector]"

# Async wrappers
pip install "whoosh-ng[async]"

# FastAPI REST API integration
pip install "whoosh-ng[api]"

# Prometheus metrics
pip install "whoosh-ng[metrics]"

# PostgreSQL backend
pip install "whoosh-ng[postgres]"

# Fuzzy matching
pip install "whoosh-ng[fuzzy]"

# Phonetic search
pip install "whoosh-ng[phonetic]"

# All optional features
pip install "whoosh-ng[vector,async,api,metrics,postgres,fuzzy,phonetic]"
```

### Development Installation

```bash
pip install "whoosh-ng[dev]"
```

## Documentation

- **[API Reference](https://dorel14.github.io/Whoosh-NG/en/api/overview/)** - Complete module documentation
- **[User Guides](https://dorel14.github.io/Whoosh-NG/en/guides/)** - Tutorials and best practices
- **[Examples](https://dorel14.github.io/Whoosh-NG/en/examples/)** - Runnable code examples
- **[French Documentation](https://dorel14.github.io/Whoosh-NG/fr/)** - Documentation en français

## Recent Changes in 4.0.0.dev0

### Added

- **Plugin System** (`whoosh.plugins`): `Plugin` base class and `PluginManager` with entry-point auto-discovery, version validation, conflict detection, enable/disable, and dependency management
- **Registry System** (`whoosh.registry`): Generic registry plus `StorageRegistry`, `AnalyzerRegistry`, `RankingRegistry`, `SuggestRegistry`, `VectorRegistry`, `AutocompleteRegistry`, and `BackendRegistry`
- **Middleware Pipeline** (`whoosh.middleware`): `Middleware` base class (sync + async), `MiddlewareContext`, `MiddlewareChain`, `MiddlewareRegistry`, with official `MetricsMiddleware`, `CacheMiddleware`, `CompressionMiddleware`, `EncryptionMiddleware`, and `PrometheusMiddleware`
- **Event Bus** (`whoosh.event_bus`): `EventBus` with subscribe/publish/clear
- **Hook System** (`whoosh.hooks`): `hookimpl`, `register_hook`, `call_hook`
- **Backends**: `Backend` ABC with lifecycle hooks, `FileBackend`, and `SQLiteBackend`
- **Provider Architecture**: `VectorProvider`/`VectorField`, `NumpyProvider` for vector similarity search
- **Autocomplete Plugin** (`whoosh_modern.autocomplete`): Inverted index and edge-ngram autocomplete
- **FastAPI Plugin** (`whoosh_fastapi`): REST endpoints for search, autocomplete, vector search, and health checks
- **Admin UI Plugin** (`whoosh_admin`): Dashboard for index administration
- **Entry Points**: Auto-loaded plugins under `whoosh.plugins` group

### Changed

- Distribution renamed from `whoosh-reloaded` to **`whoosh-ng`** (import namespace remains `whoosh`)
- Documentation site moved to GitHub Pages: https://dorel14.github.io/Whoosh-NG/
- **Python 3.11+ required** (dropped Python 3.9/3.10 support)
- Packaging cleaned: consolidated extras in `pyproject.toml`
- Type annotations modernized: `mypy src/whoosh` reports 0 errors, `py.typed` marker included

## Example: Simple Search

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser

# Define schema
schema = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    content=TEXT,
)

# Create index
ix = index.create_in("my_index", schema)

# Index documents
with ix.writer() as w:
    w.add_document(id="1", title="Hello World", content="Welcome to Whoosh-NG")
    w.add_document(id="2", title="Python Search", content="Fast text search library")

# Search
with ix.searcher() as s:
    qp = QueryParser("content", ix.schema)
    q = qp.parse("search library")
    results = s.search(q)
    for hit in results:
        print(hit["title"], hit.score)
```

## Example: FastAPI Integration

```python
from fastapi import FastAPI
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh_fastapi import create_app

schema = Schema(id=ID(), title=TEXT(), content=TEXT())
ix = index.create_in("docs", schema)

# Create FastAPI app with Whoosh-NG endpoints
app = create_app(ix, prefix="/api/v1")

# Endpoints available:
# GET  /api/v1/health          - Health check
# POST /api/v1/search          - Full-text search
# GET  /api/v1/autocomplete?q= - Autocomplete suggestions
```

## Example: Vector Search

```bash
pip install "whoosh-ng[vector]" numpy
```

```python
from whoosh.fields import Schema, TEXT, ID, VECTOR
from whoosh.vector import VectorField
from whoosh_modern.vector.plugin import VectorPlugin
from whoosh.plugins.manager import PluginManager
import numpy as np

# Create index with vector field
schema = Schema(
    id=ID(stored=True),
    title=TEXT(stored=True),
    embedding=VECTOR(dim=384),
)

# Register vector plugin
VectorPlugin().register(PluginManager())

# Index with embeddings
ix = index.create_in("vector_db", schema)
with ix.writer() as w:
    w.add_document(
        id="doc1",
        title="Python tutorial",
        embedding=np.random.rand(384).astype(np.float32).tobytes()
    )
```

## Quality Gates

The 4.0 quality policy requires every merged PR to pass:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/whoosh
uv run pytest tests
uv run python -m build
uv run twine check dist/*
```

CI validates these checks on Windows and Linux before merge.

## Development

```bash
# Install uv (if not already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup
uv python install 3.11
uv venv --python 3.11
uv sync --extra dev

# Run tests
uv run pytest
```

## Contributing

Commits follow [Conventional Commits](https://www.conventionalcommits.org/) so `python-semantic-release` can generate versions, changelogs, tags, GitHub releases, and PyPI publications automatically.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## Maintainers

- [Sygil-Dev Organization](https://github.com/Sygil-Dev)
- Matt Chaput (original Whoosh author)

## License

BSD-2-Clause. See [LICENSE](LICENSE) for details.