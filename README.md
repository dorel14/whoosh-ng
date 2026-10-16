[![PyPI](https://img.shields.io/pypi/v/whoosh-ng.svg)](https://pypi.org/project/whoosh-ng/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/whoosh-ng.svg)](https://pypi.org/project/whoosh-ng/)
[![License](https://img.shields.io/pypi/l/whoosh-ng.svg)](https://pypi.org/project/whoosh-ng/)
[![Documentation](https://img.shields.io/badge/docs-yes-blue.svg)](https://dorel14.github.io/whoosh-ng/)

# Whoosh-NG

**Whoosh-NG** is a modern, pure-Python full-text indexing and search library. Version 5.1.0 brings a complete modernization with Python 3.11+ support, strict type annotations, optional feature profiles, and automated semantic releases.

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

## Recent Changes in 5.1.0

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
- **Configuration Engine** (`whoosh_modern.config`): `ConfigEngine` with hierarchical YAML/JSON merging, Pydantic models (`WhooshNGConfig`, `FieldConfig`), and sub-engines (`SchemaEngine`, `AnalyzerEngine`, `DataSourceEngine`, `StorageEngine`, `SearchModelEngine`, `FacetEngine`, `PluginEngine`, `APIEngine`)
- **Vector Search** (`whoosh_modern.vector`): `HnswlibProvider` for HNSW approximate nearest neighbor search alongside `NumpyProvider`
- **Embedding Framework** (`whoosh_modern.embeddings`): `EmbeddingProvider` protocol, `FastEmbedProvider` with automatic model selection (`"fast"` preset), `ProviderPool` for parallel inference, `ONNXEmbeddingProvider` with CUDA support, and `model_preload` utilities
- **EmbeddingBatchWriter v4.0** (`whoosh_modern.indexing`): High-performance batch writer with provider pooling, thread-safe LRU cache, strict error handling, dimension validation, in-place document mutation, and performance metrics via `get_stats()`
- **EmbeddingMiddleware v4.0** (`whoosh_modern.middleware`): Batch accumulation mode with `embed_batch()` for +33% throughput, configurable `batch_size`, and strict error handling
- **Vector Providers v4.0** (`whoosh_modern.vector`): `NumpyProvider` with vectorized matrix multiplication and lazy consolidation; `HnswlibProvider` with batch add and adaptive ef
- **Modern N-Gram Framework** (`whoosh_modern.analysis`): `AutoCompleteAnalyzer`, `EdgeNgramAnalyzer`, `SEARCH_AS_YOU_TYPE` field type, `NgramProfiler` for performance profiling, and `AnalyzerPresets` (autocomplete, partial_match, fuzzy, code_search, documentation, ecommerce, blog, multilingual)
- **Language Auto-Detection** (`whoosh_modern.linguistics.detection`): `StopwordDetector` and `LangDetectProvider` for automatic language detection with configurable supported languages
- **Language Registry** (`whoosh_modern.linguistics.registry`): `LanguageRegistry`, `StemmerRegistry`, and `LanguageProfile` for centralized language/analyzer/stemmer resolution with `get_default_registry()`
- **Multi-Language Analyzer** (`whoosh_modern.linguistics.analyzers`): `MultiLanguageAnalyzer` applies multiple language analyzers simultaneously for multilingual indexing
- **Analyzer Presets** (`whoosh_modern.analysis.stemmer_presets`): `AnalyzerPresets.documentation()`, `.ecommerce()`, `.blog()`, `.multilingual()` for common search scenarios
- **Explain Analyzer** (`whoosh_modern.linguistics.explain`): `ExplainAnalyzer`, `AnalysisExplanation`, and `TokenExplanation` expose the tokenization/stemming pipeline for Search Studio
- **Cached Stemming Analyzer** (`whoosh_modern.analysis.cached_stemming_analyzer`): `CachedStemmingAnalyzer` wraps language analyzers with LRU caching (default `cache_size=50000`) for repeated tokens
- **Dictionary Stem Override** (`whoosh_modern.linguistics.dictionary_stem_override`): `DictionaryStemOverride` allows overriding Snowball stemming with business dictionaries (JSON/Wiktionary)
- **Stemmer Profiler** (`whoosh_modern.profiling.stemmer_profiler`): `StemmerProfiler` and `StemmerProfilerReport` measure vocabulary reduction, estimated index size reduction, and average stemming time
- **Multilingual SearchApplication** (`whoosh_modern.application`): `SearchApplication` now accepts `language_detector` and `dictionary_stem_overrides` parameters; `FieldConfig` supports `language="auto"` with detector resolution
- **Hybrid Search** (`whoosh_modern.searching`): `HybridSearcher` fuses BM25 and vector results using weighted merge or Reciprocal Rank Fusion (RRF)
- **EmbeddingBatchWriter** (`whoosh_modern.indexing`): Batch writer that generates embeddings during indexing via `VECTOR` fields, avoiding a second pass over documents
- **Searcher Configuration** (`whoosh_modern.config`): `SearcherConfig` and `SearcherEngine` allow configuring the Whoosh searcher (e.g. `weighting`) through YAML/JSON config or `SearchApplication`

### Breaking Changes

> **Re-indexing required.** The on-disk posting format in `W3TermInfo` and position/char encoding in `Formats` has changed. Indexes created with pre-2.0 versions are **not readable** by this release. Delete old index directories and re-create them.

- `Token` now uses `__slots__`: code that iterates `token.__dict__` should use `token.copy()` or slot introspection instead
- `finish_postings()` signature changed: `allow_compact=True` keyword added
- **`whoosh_modern` package structure changed**: Import paths for data sources have been updated. For example, `from whoosh_modern.data_sources import SQLSource` should now be `from whoosh_modern.data_sources.sql import SQLSource`. Please update your import statements accordingly.
- **Import path change**: The project was renamed from `whoosh-reloaded` to `whoosh-ng`.
  The modern extension modules previously available under `whoosh_reloaded` are now importable under `whoosh_modern`.
  Existing code using `whoosh_reloaded` must be updated to `whoosh_modern`. Core Whoosh
  components remain available under the `whoosh` namespace.

### Changed

- Distribution is now **`whoosh-ng`** (import namespace remains `whoosh` for core components, `whoosh_modern` for extensions)
- Documentation links now absolute (GitHub Pages): `https://dorel14.github.io/whoosh-ng/en/...`
- **Python 3.11+ required** (dropped Python 3.9/3.10 support)
- Packaging cleaned: consolidated extras in `pyproject.toml`
- Type annotations modernized: `pyright src/whoosh` reports 0 errors, `py.typed` marker included

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

## Example: SearchApplication with Searcher Config

```python
from whoosh_modern import SearchApplication
from whoosh_modern.config.models import WhooshNGConfig, SearchConfig, SearcherConfig
from whoosh_modern.storage import FileStorage

# Configure searcher weighting via config
config = WhooshNGConfig(
    search=SearchConfig(
        searcher=SearcherConfig(weighting="BM25F"),
    ),
)

app = SearchApplication(
    source=...,
    storage=FileStorage("indexdir"),
    config=config,
)
app.build()

# search() automatically uses BM25F weighting
results = app.search("python search")
```

You can also pass the searcher config directly:

```python
app = SearchApplication(
    source=...,
    storage=FileStorage("indexdir"),
    searcher={"weighting": "BM25F"},
)
```

## Example: Vector Search with FastEmbed

```bash
pip install "whoosh-ng[vector]"
```

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, VECTOR
from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider
from whoosh_modern.vector.numpy_provider import NumpyProvider

# Auto-select fastest available model (bge-small or arctic-embed-s)
provider = FastEmbedProvider(model_name="fast")

schema = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    body=TEXT(stored=True),
    body_vector=VECTOR(dimension=provider.dimension),
)

ix = index.create_in("vector_db", schema)

with ix.writer() as w:
    docs = [
        {"id": "1", "title": "Python tutorial", "body": "Learn Python programming"},
        {"id": "2", "title": "Java guide", "body": "Java development guide"},
    ]
    for doc in docs:
        vector = provider.embed(doc["body"])
        doc["body_vector"] = vector
        w.add_document(**doc)

# Search by vector similarity
query_vector = provider.embed("Python programming")
vector_provider = NumpyProvider()
vector_provider.add([(doc["id"], provider.embed(doc["body"])) for doc in docs])
hits = vector_provider.search(query_vector, k=10)
for hit in hits:
    print(hit.doc_id, hit.score)
```

## Example: Hybrid Search (BM25 + Vector)

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, VECTOR
from whoosh.qparser import QueryParser
from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider
from whoosh_modern.searching.hybrid import HybridSearcher
from whoosh_modern.vector.numpy_provider import NumpyProvider

schema = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    body=TEXT(stored=True),
    body_vector=VECTOR(dimension=384),
)

ix = index.create_in("hybrid_db", schema)
embedding_provider = FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")
vector_provider = NumpyProvider()

with ix.writer() as w:
    docs = [
        {"id": "1", "title": "Python tutorial", "body": "Learn Python programming"},
        {"id": "2", "title": "Java guide", "body": "Java development guide"},
    ]
    for doc in docs:
        vector = embedding_provider.embed(doc["body"])
        doc["body_vector"] = vector
        w.add_document(**doc)
        vector_provider.add([(doc["id"], vector)])

with ix.searcher() as searcher:
    hs = HybridSearcher(searcher, vector_provider, id_field="id")
    results = hs.search("Python programming", query_vector=embedding_provider.embed("Python programming"))
    for r in results:
        print(r.doc_id, r.score, r.bm25_score, r.vector_score)
```

## Example: Batch Indexing with Embeddings

```python
from whoosh_modern.indexing import EmbeddingBatchWriter
from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider

# Auto-select fastest model + parallel workers
provider = FastEmbedProvider(model_name="fast")

writer = EmbeddingBatchWriter(
    index,
    embedding_provider=provider,
    text_field="body",
    vector_field="body_vector",
    batch_size=500,
    embedding_batch_size=32,   # texts per embed_batch() call
    workers=2,                  # parallel embedding threads
    encoding="bytes",            # compact storage via numpy.tobytes()
)

for batch in source.stream_batches(batch_size=500):
    writer.add_batch(batch)

writer.close()

# View performance metrics
stats = writer.get_stats()
print(f"Cache hit rate: {stats['cache']['hit_rate_percent']}%")
print(f"Throughput: {stats['docs_per_second']} docs/sec")
```

## Example: Parallel Embedding with ProviderPool

```python
from whoosh_modern.embeddings.provider_pool import ProviderPool
from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider
from whoosh_modern.indexing import EmbeddingBatchWriter

# Create a pool of 4 provider instances for parallel embedding
pool = ProviderPool(
    provider_factory=lambda: FastEmbedProvider(model_name="fast"),
    pool_size=4,
)

writer = EmbeddingBatchWriter(
    index,
    embedding_provider=pool,
    text_field="body",
    vector_field="body_vector",
    batch_size=500,
)

for batch in source.stream_batches(batch_size=500):
    writer.add_batch(batch)
writer.close()
```

## Example: ONNX with CUDA

```python
from whoosh_modern.embeddings.onnx_provider import ONNXEmbeddingProvider

provider = ONNXEmbeddingProvider(
    model_path="models/bge-small-en-v1.5.onnx",
    tokenizer_dir="models/tokenizer",
    use_cuda=True,                    # auto-detect CUDA, fallback CPU
    intra_op_num_threads=2,           # ONNX Runtime thread tuning
    graph_optimization_level="all",   # enable all optimizations
)
```
