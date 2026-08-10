---
title: "Modern API"
sidebar_position: 190
---

# Modern API

The `whoosh_modern` package provides the modern, fully-typed surface of
Whoosh-NG. It includes data sources, schema discovery, validation,
middleware, profiling, autocomplete, vector search integration, and an
optimized batch writer.

## Data Sources

```python
from whoosh_modern.data_sources import (
    DataSource,
    SQLSource,
    RESTSource,
    FastCSVSource,
    JSONSource,
    GraphQLSource,
    PydanticSource,
    PandasSource,
    PolarsSource,
    ParquetSource,
    PeeweeSource,
    TortoiseSource,
    SQLAlchemySource,
    ObservableDataSource,
    DataSourceConfig,
)
```

### DataSource Protocol

The `DataSource` protocol defines the interface for all data source
implementations:

```python
class DataSource(Protocol):
    @property
    def name(self) -> str
    def discover_schema(self) -> Schema
    def iter_documents(self) -> Iterator[Document]
    def stream_batches(self, batch_size=1000) -> Iterator[list[dict]]
    def health_check(self) -> bool
```

Additional capability protocols are available:
- `IncrementalDataSource` — supports `iter_changes(since)` for incremental sync
- `AsyncDataSource` — supports `aiter_documents()` for async iteration
- `RefreshableDataSource` — supports `refresh()`
- `CountableDataSource` — supports `document_count()`
- `MetadataDataSource` — supports `metadata()`
- `ObservableDataSource` — supports `add_observer()`/`remove_observer()`

### SQLSource

```python
from whoosh_modern.data_sources import SQLSource

source = SQLSource(
    connection=conn,
    query="SELECT * FROM articles WHERE status='published'",
    incremental_field="updated_at",
    id_field="id",
    pool_size=5,
)
schema = source.discover_schema()
docs = list(source.iter_documents())
batches = list(source.stream_batches(batch_size=1000))
count = source.document_count()
meta = source.metadata()
```

### RESTSource

```python
from whoosh_modern.data_sources import RESTSource

source = RESTSource(
    url="https://api.example.com/v2/products",
    method="GET",
    pagination="page",  # or "offset", "cursor"
    page_size=50,
    headers={"Authorization": "Bearer token"},
    auth={"type": "bearer", "token": "..."},
    document_path="results",  # Extract from nested response
)
schema = source.discover_schema()
docs = list(source.iter_documents())
```

### DataSourceConfig

Declarative configuration with a factory:

```python
from whoosh_modern.data_sources import DataSourceConfig

config = DataSourceConfig(
    type="sql",
    connection=conn,
    query="SELECT * FROM articles",
    sequential_field="updated_at",
)
source = config.create()  # Returns a configured SQLSource
```

Supported types: `sql`, `sqlalchemy`, `rest`, `csv`, `json`, `graphql`,
`pydantic`, `pandas`, `polars`, `parquet`, `peewee`, `tortoise`.

## Schema Discovery

```python
from whoosh_modern.schema_discovery import SchemaDiscovery

# From column metadata (list of (name, sql_type) tuples)
columns = [("id", "INTEGER"), ("title", "TEXT"), ("published", "TIMESTAMP")]
schema = SchemaDiscovery.from_result_set(columns)

# From sample documents (auto-detects types)
schema = SchemaDiscovery.from_sample(docs)

# Optimized variant (drops non-searchable TEXT, infers IDs/booleans)
schema = SchemaDiscovery.from_sample_optimized(docs, searchable_text=["title", "content"])

# Detect ID field from schema
id_field = SchemaDiscovery.detect_id_field(dict(schema))
```

### SQL Type Mapping

`SchemaDiscovery` includes a built-in SQL type map: `VARCHAR`→`TEXT`,
`INTEGER`→`NUMERIC`, `BOOLEAN`→`BOOLEAN`, `TIMESTAMP`→`DATETIME`, `JSON`→
`KEYWORD`, `UUID`→`ID`, etc.

## FacetManager

```python
from whoosh_modern.facets import FacetManager, TermsFacet, RangeFacet, DateRangeFacet

manager = FacetManager(schema)
# Or with manual config:
manager = FacetManager(schema, config={"price": {"type": "range", "buckets": [...]}})

facets = manager.get_facets()          # Auto-discovered + manual facets
config = manager.get_facet_config("category")
stats = manager.get_facet_stats()
manager.set_manual_override("price", {"type": "range", "buckets": ["0-100", "100-500"]})
```

Auto-discovery rules:
- `TEXT`, `KEYWORD`, `BOOLEAN`, `ID` → `TermsFacet`
- `NUMERIC` → `RangeFacet`
- `DATETIME` → `DateRangeFacet`

## Validation Framework

```python
from whoosh_modern.validation import ValidationFramework, ValidationResult

validator = ValidationFramework()
results = validator.validate(source)

for result in results:
    print(f"Level {result.level}: passed={result.passed}")
    for warning in result.warnings:
        print(f"  Warning: {warning}")
    for error in result.errors:
        print(f"  Error: {error}")
```

Four validation levels:

| Level | Method | Purpose |
|-------|--------|---------|
| 1 | `validate_structural()` | DataSource availability, schema detection |
| 2 | `validate_search()` | Indexable fields, term vectors, searchable analyzers |
| 3 | `validate_performance()` | Performance warnings (e.g., TEXT fields on large datasets) |
| 4 | `validate_runtime()` | Sample iteration, type conformance |

## Middleware Pipeline

```python
from whoosh_modern.middleware import (
    Middleware,
    MiddlewarePipeline,
    RetryMiddleware,
    LoggingMiddleware,
    CacheMiddleware,
)

pipeline = MiddlewarePipeline(
    RetryMiddleware(attempts=3, backoff="exponential", jitter=True),
    LoggingMiddleware(level=logging.INFO),
    CacheMiddleware(maxsize=128),
)

def my_operation():
    return searcher.search(query)

result = pipeline.execute(my_operation)
```

### Middleware Types

- **`Middleware`**: The core base class (`whoosh.middleware.base.Middleware`, re-exported from `whoosh_modern.middleware`). Subclass it and implement the lifecycle hooks (`before_index`, `after_index`, `before_search`, `after_search`, `on_error`, `on_commit`). `RetryMiddleware`, `LoggingMiddleware`, and `CacheMiddleware` additionally keep a `wrap(operation)` helper for decorating callables.
- **`RetryMiddleware`**: Retries failed operations with exponential or linear
  backoff, with optional jitter.
- **`LoggingMiddleware`**: Logs execution time and errors.
- **`CacheMiddleware`**: Caches results keyed by operation name and arguments.
  Exposes `stats` property and `clear()` method.

## SearchView

```python
from whoosh_modern.views import SearchView

view = SearchView(
    name="articles",
    source=source,
    fields={"title": fields.TEXT(stored=True)},  # Field type overrides
    facets={"category": {"type": "terms", "limit": 50}},
    incremental_field="updated_at",
    strict=False,  # Raise on validation failures
    middleware=[LoggingMiddleware()],
    schema_version="1.0",
)

ix = view.build("indexdir")       # Create/populate index
count = view.reindex()            # Full reindex
count = view.refresh()            # Incremental refresh
results = view.validate()         # Run validation
view.evolve_schema({"new_field": fields.TEXT})  # Add fields without reindexing
```

## Optimized Writer

```python
from whoosh_modern.writer import ModernIndex

# Create or open an optimized index
index = ModernIndex.create("indexdir", schema=my_schema)
# Or open existing:
# index = ModernIndex.open("indexdir")

# Optimized writer for batch processing millions of docs
with index.writer(batch_size=5000, limitmb=512, multisegment=True) as writer:
    for batch in source.stream_batches(batch_size=5000):
        writer.add_batch(batch)
        # Or: writer.add_batches(source.stream_batches(batch_size=5000))

print(f"Documents indexed: {writer.doc_count}")

# Access searcher
with index.searcher() as searcher:
    results = searcher.search(query)
```

### Key Optimizations

- **Multisegment mode**: No merging during indexing (set with
  `multisegment=True`)
- **Reduced Python overhead**: Batch-oriented add API
- **Configurable memory limits**: `limitmb` parameter controls buffering

## Analysis Extensions

```python
from whoosh_modern.analysis import StemmingAnalyzer, get_stemmer, register_stemmer
```

### StemmingAnalyzer

Enhanced analyzer with pluggable stemmer backends:

```python
# Auto-detect best available stemmer
analyzer = StemmingAnalyzer(stemmer="auto")

# Explicit internal stemmer
analyzer = StemmingAnalyzer(stemmer="internal")

# PyStemmer (requires pip install whoosh-ng[fast-stemming])
analyzer = StemmingAnalyzer(stemmer="pystemmer")

# Custom stemmer provider
analyzer = StemmingAnalyzer(stemmer=my_custom_stemmer)

# Full parameters
analyzer = StemmingAnalyzer(
    expression=r"\S+",
    stoplist=None,
    minsize=2,
    maxsize=None,
    gaps=False,
    stemmer="auto",
    ignore=None,
    cachesize=50000,
)
```

### Stemmer Providers

```python
from whoosh_modern.analysis import get_stemmer, list_available_backends

# Get a stemmer provider
stemmer = get_stemmer("auto", "english")
stemmed = stemmer.stem("running")  # "run"

# List available backends
backends = list_available_backends()
# {"internal": "available", "pystemmer": "not installed"}

# Register a custom stemmer
@register_stemmer("my_stemmer")
class MyStemmer:
    def stem(self, word: str) -> str:
        return word.lower()

# Priority: PyStemmer > Internal (whoosh.lang)
```

### StemmerProvider Protocol

```python
class StemmerProvider(Protocol):
    def stem(self, word: str) -> str
    @property
    def name(self) -> str
    @property
    def language(self) -> str
```

Available providers:
- `InternalStemmerProvider` — wraps Whoosh's built-in `whoosh.lang.porter.stem`
- `PyStemmerProvider` — wraps the PyStemmer library (fastest)
- `IdentityStemmerProvider` — no-op stemmer for testing

## Autocomplete

```python
from whoosh_modern.autocomplete import create_autocomplete

# Create an autocomplete provider
provider = create_autocomplete("inverted")

# Add phrases
provider.add(["hello world", "hello there", "goodbye world"])

# Search
hits = provider.search("hello", limit=10)
for hit in hits:
    print(hit.text, hit.score)
```

### Classes

- **`AutocompleteHit`**: Simple data class with `text` and `score` attributes.
- **`AutocompleteProvider` (Plugin)**: Abstract base for autocomplete
  implementations. Implements `add()` and `search()`.
- **`InvertedIndexAutocomplete`**: Default provider using prefix matching with
  a scoring function favoring exact prefix matches.

## Exceptions

```python
from whoosh_modern.exceptions import (
    DataSourceError,
    DataSourceNotFoundError,
    DocumentIterationError,
    SchemaDiscoveryError,
    ValidationError,
)
```

All exceptions inherit from `DataSourceError`, which carries optional
`source` and `field` context attributes.

## Storage Providers

```python
from whoosh_modern.storage import (
    FileStorage,
    AsyncFileStorage,
    S3Storage,
    HybridStorage,
    AsyncHybridStorage,
)
```

### FileStorage

Local filesystem storage. `FileStorage` is an alias of `FileStorageProvider`. Keys are
relative paths under ``root``.

```python
from whoosh_modern.storage import FileStorage

storage = FileStorage("indexdir")
storage.write("segment_1.dat", b"data")
assert storage.read("segment_1.dat") == b"data"
assert storage.exists("segment_1.dat") is True
storage.delete("segment_1.dat")
keys = storage.list_keys()
```

### AsyncFileStorage

Async variant of ``FileStorage``. All operations run on a worker thread
via ``asyncio.to_thread``.

```python
import asyncio
from whoosh_modern.storage import AsyncFileStorage

storage = AsyncFileStorage("indexdir")

async def main() -> None:
    await storage.awrite("segment_1.dat", b"data")
    data = await storage.aread("segment_1.dat")
    await storage.adelete("segment_1.dat")

asyncio.run(main())
```

## See Also

- [Storage Providers Guide](../modern/storage-providers.md) — Storage backend integration and benchmarks
- [Provider Integration Guide](../modern/provider-integration.md) — Complete pipeline guide for all providers
- [Middleware Guide](../modern/middleware-pipeline.md) — Pipeline hooks and provider adapters
- [Stemming Guide](../modern/stemming-providers.md) — Stemmer provider integration
- [Vector Search Guide](../modern/vector.md) — Vector provider integration
- [Autocomplete Guide](../modern/autocomplete-providers.md) — Autocomplete provider integration
### S3Storage

S3-compatible blob storage. ``boto3`` is required only when this provider
is used; it is imported lazily so the rest of Whoosh-NG does not depend on
it. A ``client`` may be injected for testing.

```python
from whoosh_modern.storage import S3Storage

storage = S3Storage(bucket="my-index-bucket", prefix="segments")
storage.write("segment_1.dat", b"data")
data = storage.read("segment_1.dat")
keys = storage.list_keys()
```

### HybridStorage

Compose a local cache with a remote backend for cloud-native indexes.
The remote is the source of truth; the local cache is a write-through
performance layer.

```python
from whoosh_modern.storage import HybridStorage, S3Storage

remote = S3Storage(bucket="my-index-bucket", prefix="segments")
storage = HybridStorage(local_cache="./cache", remote=remote)

storage.write("segment_1.dat", b"data")
data = storage.read("segment_1.dat")  # served from cache after first read
storage.invalidate("segment_1.dat")   # force refresh from remote
storage.prefetch(["segment_2.dat"])   # warm cache proactively
```

Read path:

1. local cache hit → return immediately
2. cache miss → read from remote, write-through into cache, return

Write path:

- ``remote.write(key, data)`` (source of truth)
- on success → ``local_cache.write(key, data)``
- on failure → raise before polluting cache

### AsyncHybridStorage

Async variant of ``HybridStorage``. Remote operations are executed on a
worker thread via ``asyncio.to_thread`` so the event loop is never blocked.

```python
import asyncio
from whoosh_modern.storage import AsyncHybridStorage, S3Storage

remote = S3Storage(bucket="my-index-bucket", prefix="segments")
storage = AsyncHybridStorage(local_cache="./cache", remote=remote)

async def main() -> None:
    await storage.awrite("segment_1.dat", b"data")
    data = await storage.aread("segment_1.dat")
    await storage.adelete("segment_1.dat")

asyncio.run(main())
```
