[![PyPI](https://img.shields.io/pypi/v/whoosh-ng.svg)](https://pypi.org/project/whoosh-ng/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/whoosh-ng.svg)](https://pypi.org/project/whoosh-ng/)
[![License](https://img.shields.io/pypi/l/whoosh-ng.svg)](https://pypi.org/project/whoosh-ng/)
[![Documentation](https://img.shields.io/badge/docs-yes-blue.svg)](https://dorel14.github.io/whoosh-ng/)

# Whoosh-NG

**Whoosh-NG** is a modern, pure-Python full-text indexing and search library. Version 4.2.3 brings a complete modernization with Python 3.11+ support, strict type annotations, optional feature profiles, and automated semantic releases.

## Quick Start

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

# Profiling tools (psutil, re2, pystemmer)
pip install "whoosh-ng[profiling]"

# Fast stemming with PyStemmer C backend
pip install "whoosh-ng[fast-stemming]"

# All optional features
pip install "whoosh-ng[vector,async,api,metrics,postgres,fuzzy,phonetic,profiling,fast-stemming]"
```

### Development Installation

```bash
pip install "whoosh-ng[dev]"
```

## Documentation

- **[Documentation](https://dorel14.github.io/whoosh-ng/)** — Full documentation site (English)
- **[API Reference](https://dorel14.github.io/whoosh-ng/api/overview)** — Complete module documentation
- **[Examples](https://dorel14.github.io/whoosh-ng/examples/basic-indexing)** — Runnable code examples
- **[Data Sources](https://dorel14.github.io/whoosh-ng/examples/data-sources)** — SQL, REST, GraphQL, CSV, JSON, Parquet data sources
- **[Changelog](https://dorel14.github.io/whoosh-ng/core/changelog)** — Release notes and version history
- **[French Documentation](https://dorel14.github.io/whoosh-ng/fr/core/quickstart)** — Documentation en français
- **LLM-Friendly Docs**: [`llms.txt`](https://dorel14.github.io/whoosh-ng/llms.txt) (index) | [`llms-full.txt`](https://dorel14.github.io/whoosh-ng/llms-full.txt) (complete API)

## Recent Changes in 4.2.3

### Performance Highlights

| Gain | Scope | Notes |
|---|---|---|
| +68% indexing speed | 20k docs | `analyzing` phase reduced from 8.6s to 2.7s |
| +35% token creation | per-document | `Token` migrated to `__slots__` |
| -93% write_block calls | 20k docs | Field cache inline in `W3PostingsWriter` |
| Compact postings | all segments | Single-posting and short-inline fast paths |
| Global compiled regex | `RegexTokenizer` | Default pattern compiled once at module load |
| Stemmer provider | `StemmingAnalyzer` | Select `auto`/`internal`/`pystemmer` backends |

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
- **Data Sources** (`whoosh_modern.data_sources`): `DataSource` protocol with `ObservableDataSource`, `SQLSource` (connection pooling, GROUP BY/JOIN/incremental sync), `SQLAlchemySource`, `RESTSource` (page/offset/cursor pagination + auth), `GraphQLSource`, `FastCSVSource`, `JSONSource`, `ParquetSource`, `PandasSource`, `PolarsSource`, `PeeweeSource`, `TortoiseSource`, `PydanticSource`, and `DataSourceConfig` for declarative config from dict/JSON/YAML files
- **Schema Discovery** (`whoosh_modern.schema_discovery`): Result-set introspection with duplicate column detection and JSON/JSONB handling
- **FacetManager** (`whoosh_modern.facets`): Auto-discovery of facetable fields with manual override support
- **Validation Framework** (`whoosh_modern.validation`): 4-level validation (STRICT/WARN/SKIP/NONE) with typed exceptions and field context
- **Middleware Pipeline** (`whoosh_modern.middleware`): `RetryMiddleware`, `LoggingMiddleware`, `CacheMiddleware` with chainable pipeline
- **SearchView** (`whoosh_modern.views`): Unified interface integrating data sources, schema discovery, facets, validation, and middleware with `build()`, `refresh()`, `reindex()`, `validate()`, `evolve_schema()`, and strict mode
- **Stemmer Provider System** (`whoosh_modern.analysis`): `get_stemmer()`, `register_stemmer()`, auto-detection between internal Porter stemmer and PyStemmer C backend
- **Enhanced StemmingAnalyzer** (`whoosh_modern.analysis`): Accepts `stemmer="auto"|"internal"|"pystemmer"|provider` parameter

### Breaking Changes

> **Re-indexing required.** The on-disk posting format in `W3TermInfo` and position/char encoding in `Formats` has changed. Indexes created with pre-2.0 versions are **not readable** by this release. Delete old index directories and re-create them.

- `Token` now uses `__slots__`: code that iterates `token.__dict__` should use `token.copy()` or slot introspection instead
- `finish_postings()` signature changed: `allow_compact=True` keyword added
- **`whoosh_modern` package structure changed**: Import paths for data sources have been updated. For example, `from whoosh_modern.data_sources import SQLSource` should now be `from whoosh_modern.data_sources.sql import SQLSource`. Please update your import statements accordingly.

### Changed

- Distribution renamed from `whoosh-reloaded` to **`whoosh-ng`** (import namespace remains `whoosh`)
- Documentation links now absolute (GitHub Pages): `https://dorel14.github.io/whoosh-ng/en/...`
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

## Example: Data Sources

### SQLSource — Index from a SQL database

```python
from whoosh_modern.data_sources.sql import SQLSource
from whoosh import index
from whoosh.fields import Schema, TEXT, NUMERIC
import sqlite3

conn = sqlite3.connect("mydb.db")
source = SQLSource(
    connection=conn,
    query="SELECT * FROM products",
    incremental_field="updated_at",
    id_field="id",
)

# Discover schema from actual result metadata
schema = source.discover_schema()

# Build index with SearchView
from whoosh_modern.views import SearchView
view = SearchView(name="products", source=source)
ix = view.build("indexdir")
```

### RESTSource — Index from a REST API

```python
from whoosh_modern.data_sources.rest import RESTSource

source = RESTSource(
    url="https://api.example.com/v2/products",
    pagination="page",
    page_size=50,
    headers={"Authorization": "Bearer your_token"},
)

schema = source.discover_schema()
docs = list(source.iter_documents())
```

### SearchView — Full pipeline integration

```python
from whoosh_modern.views import SearchView
from whoosh_modern.data_sources.sql import SQLSource
import sqlite3

conn = sqlite3.connect("mydb.db")
source = SQLSource(
    connection=conn,
    query="SELECT * FROM reuters_articles",
    incremental_field="article_date",
    id_field="id",
)

view = SearchView(name="reuters", source=source)
ix = view.build("indexdir")

# Incremental refresh
count = view.refresh()

# Full reindex
count = view.reindex()
```

## Example: Vector Search

```bash
pip install "whoosh-ng[vector]" numpy
```

```python
from whoosh import index
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
