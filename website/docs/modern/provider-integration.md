---
title: "Provider Integration"
sidebar_position: 85
---

# Provider Integration: Complete Pipeline Guide

Module: `whoosh_modern.storage`, `whoosh_modern.analysis.stemmer_providers`, `whoosh_modern.linguistics.synonyms`, `whoosh_modern.vector`, `whoosh_modern.autocomplete`
Version: 3.0.0

This guide explains how all Whoosh-NG providers integrate into the indexing and
search pipeline. It is the definitive reference for understanding the data flow
from raw documents to search results.

## Overview

Whoosh-NG uses a **provider pattern** to keep the core engine lean while enabling
pluggable behavior for storage, text analysis, vector search, and autocomplete.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Whoosh-NG Provider Stack                      │
│                                                                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │ Storage     │  │ Stemmer      │  │ Synonym     │  │ Vector    │ │
│  │ Providers   │  │ Providers    │  │ Providers   │  │ Providers │ │
│  │             │  │              │  │             │  │           │ │
│  │ FileStorage │  │ Internal     │  │ Static      │  │ Numpy     │ │
│  │ S3Storage   │  │ PyStemmer    │  │ YAML        │  │ HNSW      │ │
│  │ Hybrid      │  │ Identity     │  │ JSON        │  │ Faiss     │ │
│  │ SQLite      │  │ Custom       │  │ SQLite      │  │ Qdrant    │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │
│         │                │                │                │       │
│         ▼                ▼                ▼                ▼       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │              Middleware Pipeline (hooks)                         ││
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐    ││
│  │  │Storage      │  │Stemming      │  │Synonym              │    ││
│  │  │Middleware   │  │Middleware    │  │ExpansionMiddleware  │    ││
│  │  └─────────────┘  └──────────────┘  └─────────────────────┘    ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │              Whoosh Core Engine                                  ││
│  │  Index │ Writer │ Searcher │ QueryParser │ Segment files         ││
│  └─────────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

## Complete Indexing Pipeline

### Step-by-step flow

```text
┌─────────────────┐
│   DataSource    │  (SQL, JSON, REST, CSV, DataFrame, etc.)
│   .stream_batches() │
└────────┬────────┘
         │ batches of documents
         ▼
┌─────────────────┐
│  SchemaDiscovery │  Infers Whoosh Schema from data source columns
│  .discover_schema() │
└────────┬────────┘
         │ Schema(TEXT, ID, NUMERIC, VECTOR, ...)
         ▼
┌─────────────────────────────────────────┐
│  Storage Provider Resolution             │
│                                         │
│  storage._root (if any)                 │
│    └──► whoosh.index.create_in(root)    │
│  No root                                 │
│    └──► tempfile.mkdtemp() → create_in() │
└────────┬────────────────────────────────┘
         │ Index instance
         ▼
┌─────────────────────────────────────────┐
│  Writer + MiddlewareChain                │
│                                         │
│  chain.run_before("before_index")        │
│    ├── StorageMiddleware                 │
│    │   └── tags context with provider    │
│    ├── StemmingMiddleware                │
│    │   └── stems document fields         │
│    └── SynonymExpansionMiddleware        │
│        └── expands fields with synonyms  │
│                                         │
│  writer.add_document(**doc)              │
│    └── Whoosh core applies field         │
│        analyzers (TEXT.analyzer)          │
│        and writes to segment             │
│                                         │
│  writer.commit()                         │
│    └── chain.run_after("on_commit")      │
│        └── StorageMiddleware             │
│            └── writes commit checkpoint  │
└────────┬────────────────────────────────┘
         │ Segment files on disk/S3/cache
         ▼
┌─────────────────┐
│  Whoosh Index    │
│  (segments)      │
└─────────────────┘
```

### Concrete example

```python
from whoosh import index, fields
from whoosh_modern import (
    SearchApplication,
    SQLSource,
    HybridStorage,
    S3Storage,
    StemmingAnalyzer,
    get_stemmer,
    SynonymManager,
    SynonymExpansionMiddleware,
    StorageMiddleware,
    StemmingMiddleware,
)
from sqlalchemy import create_engine

# 1. Data source
engine = create_engine("sqlite:///products.db")
source = SQLSource(query="SELECT id, name, description FROM products", connection=engine)

# 2. Storage
remote = S3Storage(bucket="my-index-bucket", prefix="segments")
storage = HybridStorage(local_cache="./cache", remote=remote)

# 3. Schema (auto-discovered from SQL columns)
#    But we customize the analyzer
stemmer = get_stemmer("auto", "english")
schema = fields.Schema(
    name=fields.TEXT(analyzer=StemmingAnalyzer(stemmer=stemmer), stored=True),
    description=fields.TEXT(analyzer=StemmingAnalyzer(stemmer=stemmer)),
    id=fields.ID(stored=True, unique=True),
)

# 4. Create index in storage root
ix = index.create_in(storage._cache_root, schema)

# 5. Build middleware chain
syn_manager = SynonymManager({"laptop": ["notebook", "portable"]})
chain = MiddlewareChain([
    StorageMiddleware(storage, name="products"),
    StemmingMiddleware(stemmer=stemmer.stem),
    SynonymExpansionMiddleware(syn_manager),
])

# 6. Index with middleware
with MiddlewareWriter(ix.writer(), chain) as writer:
    for batch in source.stream_batches():
        for doc in batch:
            writer.add_document(**doc)
    writer.commit()
```

## Complete Search Pipeline

### Step-by-step flow

```text
┌─────────────────┐
│   User Query    │  "running cats"
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  MiddlewareChain.run_before("search")    │
│                                         │
│  ├── StemmingMiddleware                  │
│  │   └── "running cats" → "run cat"      │
│  ├── SynonymExpansionMiddleware          │
│  │   └── "run cat" → "run cat running feline" │
│  └── QueryRewriteMiddleware              │
│      └── custom rewrites                 │
└────────┬────────────────────────────────┘
         │ Modified query
         ▼
┌─────────────────────────────────────────┐
│  QueryParser.parse(query)                │
│    └── Query object (Term, And, Or...)  │
└────────┬────────────────────────────────┘
         │ Query object
         ▼
┌─────────────────────────────────────────┐
│  Searcher.search(query)                  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Keyword search path              │  │
│  │  └── reads posting lists from     │  │
│  │      segment files                │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Vector search path (if VECTOR)   │  │
│  │  └── VectorRegistry.get(provider) │  │
│  │      └── NumpyProvider.search()   │  │
│  │          └── cosine similarity    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Autocomplete path                │  │
│  │  └── AutocompleteRegistry.get()   │  │
│  │      └── provider.suggest()       │  │
│  └───────────────────────────────────┘  │
└────────┬────────────────────────────────┘
         │ Raw Results
         ▼
┌─────────────────────────────────────────┐
│  MiddlewareChain.run_after("search")     │
│                                         │
│  └── RankingMiddleware                   │
│      └── re-sorts results                │
└────────┬────────────────────────────────┘
         │ Final Results
         ▼
┌─────────────────┐
│  Hits returned   │
└─────────────────┘
```

### Concrete example

```python
from whoosh.qparser import QueryParser
from whoosh_modern.middleware import (
    StemmingMiddleware,
    RankingMiddleware,
    QueryRewriteMiddleware,
)
from whoosh_modern.analysis import get_stemmer
from whoosh_modern.vector import NumpyProvider
from whoosh_modern.vector.plugin import VectorPlugin
from whoosh.plugins.manager import PluginManager
import numpy as np

# 1. Setup plugins at startup
manager = PluginManager()
VectorPlugin().register(manager)

# 2. Open index
ix = index.open_dir("indexdir")

# 3. Build middleware chain
stemmer = get_stemmer("auto", "english")
chain = MiddlewareChain([
    StemmingMiddleware(stemmer=stemmer.stem),
    QueryRewriteMiddleware(rewriter=lambda q: q + " portable"),  # add synonym
    RankingMiddleware(ranker=lambda r: sorted(r, key=lambda h: h.score, reverse=True)),
])

# 4. Search with middleware
with MiddlewareSearcher(ix.searcher(), chain) as searcher:
    # Query is transformed by middleware before execution
    results = searcher.search("laptop")
    for hit in results:
        print(f"{hit['name']}: {hit.score:.4f}")

    # 5. Vector search (parallel)
    query_vec = np.random.rand(384).tolist()
    vector_results = searcher.vector_search("embedding", query_vec, limit=10)
    for hit in vector_results:
        print(f"doc_id={hit.doc_id}, score={hit.score:.4f}")
```

## Provider Comparison Matrix

| Aspect | Storage | Stemmer | Synonym | Vector | Autocomplete |
|--------|---------|---------|---------|--------|--------------|
| **Integration point** | `StorageMiddleware` + `create_in()` | `StemmingAnalyzer` (field) + `StemmingMiddleware` | `SynonymExpansionMiddleware` | `VectorRegistry` + segment format | `AutocompleteRegistry` + standalone |
| **Registration** | Manual or `__getattr__` | `register_stemmer()` decorator | `SynonymManager` CRUD | `VectorPlugin.register()` | `AutocompletePlugin.register()` |
| **Used at index time** | Yes (commit checkpoints) | Yes (field analyzer + middleware) | Yes (before_index) | Yes (VECTOR field) | No (standalone or post-index) |
| **Used at search time** | Yes (segment reads via filesystem) | Yes (field analyzer + middleware) | Yes (before_search) | Yes (vector_search) | Yes (suggest/search) |
| **Persistence** | Segment files / S3 / SQLite | In-memory (stateless) | In-memory / YAML / JSON / SQLite | Segment files (metadata) | In-memory (phrase list) |
| **Configuration** | Provider class + kwargs | Backend name + language | Mapping dict or file | Provider name + metric | Provider type + params |

## Common Patterns

### Pattern 1: Provider as Field Analyzer

Used by: Stemmer providers, language analyzers

```python
schema = Schema(
    content=TEXT(analyzer=StemmingAnalyzer(stemmer="auto"))
)
```

The provider is wrapped in a Whoosh analyzer and applied automatically.

### Pattern 2: Provider as Middleware

Used by: Storage, Stemmer, Synonyms

```python
chain = MiddlewareChain([
    StorageMiddleware(storage),
    StemmingMiddleware(stemmer=stemmer.stem),
    SynonymExpansionMiddleware(manager),
])
```

The provider is consumed by middleware hooks in the pipeline.

### Pattern 3: Provider as Registry Entry

Used by: Vector, Autocomplete

```python
VectorRegistry.register("numpy", NumpyProvider(), owner="my_app")
provider = VectorRegistry.get("numpy", "my_app")
```

The provider is stored in a global registry and resolved by name at runtime.

### Pattern 4: Provider as Standalone Service

Used by: Autocomplete, Vector (manual mode)

```python
provider = NumpyProvider()
provider.add([(doc_id, vec)])
results = provider.search(query_vec)
```

The provider operates independently of Whoosh's index/searcher.

## Best Practices

1. **Choose the right integration pattern**: Field analyzers for static schemas, middleware for dynamic behavior, registry for pluggable backends.
2. **Avoid double-application**: Don't use both field-level analyzers and middleware for the same transformation (e.g., stemming).
3. **Register providers at startup**: Call `VectorPlugin().register(manager)` and `AutocompletePlugin().register(manager)` before creating indexes.
4. **Use the highest-level API when possible**: [`SearchApplication`](/modern/search-application) for end-to-end, `create_autocomplete()` for suggestions, `get_stemmer()` for stemming.
5. **Keep providers stateless**: Providers should not hold index-specific state; use middleware context for per-request data.
6. **Test providers in isolation**: Each provider should be testable without Whoosh core (unit tests for `provider.search()`, `provider.add()`).
7. **Document provider dependencies**: Note optional dependencies (boto3, PyStemmer, PyYAML) in your project's requirements.

## See Also

- [Storage Providers Guide](storage-providers.md) — Storage backend integration
- [Stemming Guide](../core/stemming.md) — Stemmer provider integration
- [Vector Search Guide](vector.md) — Vector provider integration
- [Autocomplete Guide](autocomplete.md) — Autocomplete provider integration
- [Middleware Guide](middleware-pipeline.md) — Pipeline hooks and provider adapters
- [Plugins Guide](plugins-advanced.md) — Plugin registration and entry points
- [API: Modern](../api/modern.md) — Full API reference for all providers
