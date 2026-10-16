---
title: "SearchApplication"
sidebar_position: 21
---

# SearchApplication

Module: `whoosh_modern.application`
Version: 3.2.0

`SearchApplication` is the **unified entry point** for Whoosh-NG. It orchestrates the full indexing and search pipeline from a `DataSource` to a searchable Whoosh index: schema discovery, validation, storage resolution, middleware composition, index creation, and query execution.

## Architecture

```text
DataSource (SQL, JSON, REST, CSV, …)
    │
    ▼
SearchApplication
    │
    ├── source.discover_schema() ──► Whoosh Schema
    │
    ├── storage._resolve_index_path() ──► filesystem path
    │       │
    │       ├── FileStorageProvider ──► provider.root
    │       └── Other providers ──► tempfile.mkdtemp()
    │
    ├── SearchView.build(path)
    │       │
    │       ├── MiddlewareChain.before_index()
    │       │   ├── StorageMiddleware
    │       │   ├── EmbeddingMiddleware (optional)
    │       │   ├── StemmingMiddleware
    │       │   └── SynonymExpansionMiddleware
    │       │
    │       ├── for doc in source.iter_documents():
    │       │       writer.add_document(**prepared_doc)
    │       │
    │       └── writer.commit()
    │
    ▼
Whoosh Index (segments on disk / S3 / hybrid cache)
```

## Quick Start

```python
from whoosh_modern import SearchApplication, SQLSource
from whoosh_modern.storage import FileStorage
import sqlite3

engine = sqlite3.connect("products.db")
app = SearchApplication(
    source=SQLSource(query="SELECT * FROM products", connection=engine),
    storage=FileStorage("indexdir"),
)
app.build()
results = app.search("laptop")
for hit in results:
    print(hit["title"])
```

## Constructor

```python
SearchApplication(
    source: DataSource | None = None,
    storage: SyncStorageProvider | None = None,
    wiktionary_indexer: WiktionaryIndexer | None = None,
    language_detector: LanguageDetector | None = None,
    dictionary_stem_overrides: dict[str, str] | None = None,
    embedding_provider: Any | None = None,
    embedding_fields: list[dict[str, str]] | None = None,
    searcher: SearcherConfig | dict[str, Any] | None = None,
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `DataSource \| None` | Data source providing documents for indexing. Required for `build()`. |
| `storage` | `SyncStorageProvider \| None` | Storage backend for index files. When it is a `FileStorageProvider`, its public `root` is used as the index directory. Otherwise a temporary directory is created. |
| `wiktionary_indexer` | `WiktionaryIndexer \| None` | Wiktionary indexer whose synonyms will be loaded into the synonym expansion middleware on first access. |
| `language_detector` | `LanguageDetector \| None` | Language detector used when `language="auto"` is set on fields. When provided, the detector is called on each document to resolve the language and inject a `_language` stored field. |
| `dictionary_stem_overrides` | `dict[str, str] \| None` | Mapping of word → stemmed form to override the default Snowball stemmer. |
| `embedding_provider` | `Any \| None` | Embedding provider used to enrich documents with dense vectors before indexing. |
| `embedding_fields` | `list[dict[str, str]] \| None` | Sequence of `{"source_field": "...", "target_field": "..."}` mappings for multi-field embedding. When provided, the `source_field` / `target_field` defaults from the embedding configuration are ignored. |
| `searcher` | `SearcherConfig \| dict[str, Any] \| None` | Optional searcher configuration. Accepts a `SearcherConfig` instance, a dict that will be converted to `SearcherConfig`, or `None` to fall back to the config object passed to the constructor. When set, `search()` opens the index with the configured weighting model. |

## Properties

### `index`

```python
@property
def index(self) -> Index
```

Returns the built Whoosh `Index`.

Raises `RuntimeError` if `build()` has not been called yet.

### `language_detector`

```python
@property
def language_detector(self) -> LanguageDetector | None
```

Returns the configured language detector, or `None` if not provided.

### `synonym_manager`

```python
@property
def synonym_manager(self) -> SynonymManager
```

Returns the `SynonymManager` populated from the Wiktionary index. If a `wiktionary_indexer` was provided at construction time, the manager is populated lazily on first access, even if `build()` has not been called yet. If no indexer was provided, an empty manager is returned.

## Methods

### `build()`

```python
def build(self) -> SearchApplication
```

Build the index from the data source.

1. Resolves the index path from the storage provider.
2. Discovers the schema from the data source.
3. Creates a `SearchView` and optionally attaches `EmbeddingMiddleware`.
4. Runs validation.
5. Creates or opens the Whoosh index.
6. Populates the index by iterating all documents.

Returns `self` for chaining.

Raises `ValueError` if no data source was provided.

### `search()`

```python
def search(self, query: Any, **kwargs: Any) -> Any
```

Search the index.

- If `query` is a string, it is parsed using `QueryParser` with the first schema field as the default field.
- When a `searcher` configuration was provided at construction time or via `config`, the index is opened with the configured `weighting` model. Otherwise the default Whoosh searcher is used.
- Delegates to `searcher.search()`.

Returns search results from the Whoosh searcher.

Raises `RuntimeError` if `build()` has not been called yet.

### With Searcher Config

```python
from whoosh_modern import SearchApplication
from whoosh_modern.config.models import WhooshNGConfig, SearchConfig, SearcherConfig
from whoosh_modern.storage import FileStorage

config = WhooshNGConfig(
    search=SearchConfig(
        searcher=SearcherConfig(weighting="BM25F"),
    ),
)

app = SearchApplication(
    source=source,
    storage=FileStorage("indexdir"),
    config=config,
)
app.build()

# search() uses BM25F weighting automatically
results = app.search("python search")
```

You can also pass the searcher configuration directly:

```python
app = SearchApplication(
    source=source,
    storage=FileStorage("indexdir"),
    searcher={"weighting": "BM25F"},
)
```

Available weighting models: `BM25F`, `BM25`, `TF_IDF`, `PL2`, `DFree`, `Frequency`.

## Usage Examples

### With Local Storage

```python
from whoosh_modern import SearchApplication, SQLSource
from whoosh_modern.storage import FileStorage
import sqlite3

engine = sqlite3.connect("products.db")
app = SearchApplication(
    source=SQLSource(query="SELECT * FROM products", connection=engine),
    storage=FileStorage("indexdir"),
)
app.build()
results = app.search("laptop")
```

### With Hybrid S3 Storage

```python
from whoosh_modern import SearchApplication, SQLSource
from whoosh_modern.storage import HybridStorage, S3Storage

remote = S3Storage(bucket="my-index-bucket", prefix="segments")
storage = HybridStorage(local_cache="./cache", remote=remote)

app = SearchApplication(
    source=SQLSource(query="SELECT * FROM products", connection=engine),
    storage=storage,
)
app.build()
results = app.search("laptop")
```

### With Language Detection

```python
from whoosh_modern import SearchApplication
from whoosh_modern.linguistics.detection import StopwordDetector
from whoosh_modern.data_sources.json import JSONSource

detector = StopwordDetector(["fr", "en", "de"])
source = JSONSource("data/products.json")

app = SearchApplication(
    source=source,
    language_detector=detector,
)
app.build()
```

When fields are configured with `language="auto"`, the detector resolves the language from the document content and injects a `_language` stored field.

### With Wiktionary Synonyms

```python
from whoosh_modern import SearchApplication
from whoosh_modern.linguistics.wiktionary_indexer import WiktionaryIndexer

indexer = WiktionaryIndexer(language="en")
indexer.build()

app = SearchApplication(
    source=source,
    wiktionary_indexer=indexer,
)
app.build()

# Access the populated synonym manager
synonym_manager = app.synonym_manager
```

### With Dictionary Stem Overrides

```python
from whoosh_modern import SearchApplication

app = SearchApplication(
    source=source,
    dictionary_stem_overrides={
        "mice": "mouse",
        "geese": "goose",
    },
)
app.build()
```

## SearchApplication vs SearchView

`SearchApplication` is a simplified wrapper around `SearchView`. Use `SearchApplication` for most production use cases. Use `SearchView` directly when you need fine-grained control over the indexing lifecycle.

| Feature | SearchApplication | SearchView |
|---------|-------------------|------------|
| Schema discovery | ✅ automatic | ✅ automatic |
| Validation | ✅ automatic | ✅ automatic |
| Incremental refresh | ❌ | ✅ `refresh()` |
| Full reindex | ❌ | ✅ `reindex()` |
| Schema evolution | ❌ | ✅ `evolve_schema()` |
| Custom middleware | ❌ | ✅ `middleware=` |
| Facets | ❌ | ✅ `facets=` |
| Field overrides | ❌ | ✅ `fields=` |
| Storage integration | ✅ automatic | ✅ via `StorageMiddleware` |

## How Storage Integration Works

When `storage` is a `FileStorageProvider` (exposed as `FileStorage`), `SearchApplication` uses its public `root` as the index directory. For all other providers (S3, Hybrid, Snapshot), it falls back to a temporary directory because Whoosh core requires a filesystem path for `create_in()`.

The actual segment routing, commit checkpointing, and cache synchronization are handled by `StorageMiddleware` at the middleware layer, not by the storage provider itself.

## Hybrid Search (BM25 + Vector)

`SearchApplication` supports hybrid search through `HybridSearcher`, which fuses BM25 keyword results with vector similarity results.

```python
from whoosh_modern import SearchApplication
from whoosh_modern.embeddings import FastEmbedProvider
from whoosh_modern.vector.numpy_provider import NumpyProvider
from whoosh_modern.searching.hybrid import HybridSearcher

provider = FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")
vector_provider = NumpyProvider()

app = SearchApplication(
    source=source,
    embedding_provider=provider,
    storage=FileStorage("indexdir"),
)
app.build("indexdir")

with app.index.searcher() as searcher:
    hs = HybridSearcher(searcher, vector_provider, id_field="id")
    query_vector = provider.embed("Python programming")
    results = hs.search(
        "Python programming",
        query_vector=query_vector,
        method="weighted",   # or "rrf" for Reciprocal Rank Fusion
        alpha=0.5,           # 0.0 = BM25 only, 1.0 = vector only
    )
    for r in results:
        print(r.doc_id, r.score, r.bm25_score, r.vector_score)
```

## Parallel Embedding with ProviderPool

For high-throughput indexing, use `ProviderPool` to parallelize embedding across multiple provider instances:

```python
from whoosh_modern.embeddings.provider_pool import ProviderPool
from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider

pool = ProviderPool(
    provider_factory=lambda: FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5"),
    pool_size=4,
)

app = SearchApplication(
    source=source,
    embedding_provider=pool,
    storage=FileStorage("indexdir"),
)
app.build("indexdir")
```

Expected improvement: parallel throughput vs single provider (benchmark on your hardware).

## See Also

- [SearchView](/examples/search-view) — Lower-level view with refresh, reindex, and validation
- [Storage Providers](/modern/storage-providers) — Pluggable storage backends
- [Middleware Pipeline](/modern/middleware-pipeline) — Cross-cutting indexing and search hooks
- [Linguistics](/modern/linguistics) — Language detection and synonym expansion
- [Provider Integration](/modern/provider-integration) — End-to-end pipeline guide
- [Auto-Indexing](/modern/auto-indexing) — Schema discovery and data-source driven indexing
