---
title: "Modern Indexing API"
nav_order: 250
---

# Modern Indexing API

Whoosh-NG provides an optimized indexing layer in `whoosh_modern.indexing` for high-throughput document ingestion. These utilities wrap the core Whoosh writer without modifying the library internals.

## BatchIndexWriter

`BatchIndexWriter` wraps a core Whoosh writer with optimizations for batch processing of large datasets.

### Key Optimizations

- Pre-computes schema field names for fast filtering (O(1) per-field validation)
- Skips fields not in the schema (avoiding per-document overhead)
- Uses `multisegment=True` to defer merging during indexing
- Supports configurable batch commits to reduce I/O pressure
- Accepts a callback for post-commit hooks

### Basic Usage

```python
from whoosh_modern.indexing import BatchIndexWriter
from whoosh import index

ix = index.open_dir("indexdir")

writer = BatchIndexWriter(ix, batch_size=5000, commit_every=10)

for batch in source.stream_batches(batch_size=5000):
    writer.add_batch(batch)

writer.close()
```

### Context Manager

```python
with BatchIndexWriter(ix, batch_size=10000) as writer:
    for doc in documents:
        writer.add_document(doc)
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `batch_size` | 5000 | Number of documents per batch |
| `limitmb` | 512 | Memory limit for the writer (MB) |
| `commit_every` | None | Commit after N batches (None = no auto-commit during indexing) |
| `multisegment` | True | Use multisegment mode to defer merging |
| `callback` | None | Callback invoked after each commit |
| `**writer_kwargs` | None | Additional keyword args passed to `index.writer()` |

### With Commit Profiler

```python
from whoosh_modern.indexing import BatchIndexWriter
from whoosh_modern.profiling import CommitProfilerV2

profiler = CommitProfilerV2()
with BatchIndexWriter(ix, batch_size=5000, commit_every=5, commit_profiler=profiler) as writer:
    for batch in source.stream_batches(batch_size=5000):
        writer.add_batch(batch)

print(profiler.report())
```

---

## AnalyzerCache

`AnalyzerCache` provides an LRU cache for analyzer results, avoiding redundant analysis work on repeated field values.

### Basic Usage

```python
from whoosh_modern.indexing import BatchIndexWriter
from whoosh_modern.profiling import AnalyzerCache

cache = AnalyzerCache(maxsize=50000)
analyzer = StandardAnalyzer()

for doc in docs:
    cache_key = f"title:{doc['title']}"
    tokens = cache.get(cache_key)
    if tokens is None:
        tokens = list(analyzer(doc['title']))
        cache.put(cache_key, tokens)
```

### With get_or_compute

```python
from whoosh_modern.profiling import AnalyzerCache

cache = AnalyzerCache(maxsize=50000)
analyzer = StandardAnalyzer()

for doc in docs:
    tokens = cache.get_or_compute(
        f"title:{doc['title']}",
        lambda: list(analyzer(doc['title']))
    )
```

### Cache Statistics

```python
cache = AnalyzerCache(maxsize=50000)
# ... use cache ...

print(f"Hit rate: {cache.hit_rate:.1%}")
print(f"Size: {cache.size}/{cache.maxsize}")
print(cache.report())
# Analyzer Cache Report
# ==================================================
#   Size: 4823/50000
#   Hits: 12543
#   Misses: 3421
#   Hit rate: 78.6%
```

### Sizing from Profiling Data

```python
from whoosh_modern.profiling import AnalyzerCache, CacheAnalyzer

analyzer = CacheAnalyzer()
analysis = analyzer.analyze(source.iter_documents())

cache = AnalyzerCache.from_profiling(analysis.to_dict())
# Creates an optimally sized cache based on field repetition ratios
```

---

## FieldAnalyzerCache

`FieldAnalyzerCache` wraps an analyzer and caches results per field, automatically generating cache keys from field name and value.

### Basic Usage

```python
from whoosh_modern.profiling import FieldAnalyzerCache

field_cache = FieldAnalyzerCache(
    analyzer=StandardAnalyzer(),
    fields=["Country", "City"],
    cache_size=50000,
)

for doc in docs:
    for field in ["Country", "City"]:
        tokens = field_cache.analyze(field, doc[field])
```

### Invalidating Cache Entries

```python
# Invalidate a specific entry
field_cache.invalidate("Country", "USA")

# Clear entire cache
field_cache.clear()
```

### Cache Statistics

```python
print(f"Hit rate: {field_cache.hit_rate:.1%}")
print(field_cache.report())
# Field Analyzer Cache Report
# ==================================================
#   Fields: ['City', 'Country']
#   Cache size: 4823/50000
#   Hit rate: 96.5%
#   Hits: 12543
#   Misses: 3421
```

---

## Available Data Sources

| Class | Type | Dependencies |
|-------|------|-------------|
| `SQLSource` | SQLite, PostgreSQL, MySQL | `sqlite3` (stdlib) |
| `SQLAlchemySource` | Any SQLAlchemy-supported DB | `sqlalchemy` |
| `RESTSource` | REST APIs | none (stdlib `urllib`) |
| `GraphQLSource` | GraphQL APIs | none (stdlib `urllib`) |
| `FastCSVSource` | CSV files | none |
| `JSONSource` | JSON/JSONL files | none |
| `ParquetSource` | Parquet files | `pyarrow` or `pandas` |
| `PandasSource` | pandas DataFrames | `pandas` |
| `PolarsSource` | Polars DataFrames | `polars` |
| `PeeweeSource` | Peewee ORM | `peewee` |
| `TortoiseSource` | Tortoise ORM | `tortoise-orm` |
| `PydanticSource` | Pydantic models | `pydantic` |
