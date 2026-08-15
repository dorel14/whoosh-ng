---
title: "Storage Providers"
sidebar_position: 210
---

# Storage Providers

Whoosh-NG provides pluggable storage backends through the
`SyncStorageProvider` / `AsyncStorageProvider` contracts. This allows the
index to be persisted on local disk, SQLite, S3, or a hybrid cache + remote
setup without changing the writer or the index.

## Architecture Overview

### Level 1: SnapshotStorage (Simple)

```
Writer → Local FS → Commit → Upload Segment → S3
Reader → Download Segment → Open locally
```

Very simple to maintain. Use `SnapshotStorage` when you want S3 as a simple
backup/restore target without the complexity of a local cache.

### Level 2: CachedObjectStorage (Recommended for Production)

```
+----------+
|  MinIO   |
+----------+
     ^
     |
 Sync |
     v
+-----------+   Cache Layer   +-----------+
| Searcher  |<--------------->| Writer    |
+-----------+                 +-----------+
        |
        v
 Local SSD
```

- Index lives on SSD
- S3 serves as replication
- Segments are pushed after commit
- Restoration possible at any moment

This is what many modern distributed search systems do.

## Available providers

| Provider | Type | Backend | Use Case |
|----------|------|---------|----------|
| `FileStorage` | sync | local filesystem | Single-node, no cloud |
| `AsyncFileStorage` | async | local filesystem | Single-node async |
| `S3Storage` | sync | S3-compatible | Direct S3 access |
| `SnapshotStorage` | sync | S3-compatible | Simple backup/restore |
| `HybridStorage` | sync | local cache + remote | **Production** (alias: `CachedObjectStorage`) |
| `AsyncHybridStorage` | async | local cache + remote | Production async |
| `CoreStorageAdapter` | sync | core `FileStorage` → modern `SyncStorageProvider` | Bridge legacy core backends into the modern pipeline |

All providers are importable from `whoosh_modern.storage`.

## FileStorage

Local filesystem storage. Keys are relative paths under `root`.

```python
from whoosh_modern.storage import FileStorage

storage = FileStorage("indexdir")
storage.write("segment_1.dat", b"data")
assert storage.read("segment_1.dat") == b"data"
assert storage.exists("segment_1.dat") is True
storage.delete("segment_1.dat")
keys = storage.list_keys()
```

## CoreStorageAdapter

Wraps a core ``whoosh.filedb.filestore.FileStorage`` instance behind the modern
``SyncStorageProvider`` interface. This lets you drop an existing core storage
backend into a modern ``HybridStorage`` or ``StorageMiddleware`` chain without
modifying the core class.

```python
from whoosh.filedb.filestore import FileStorage as CoreFileStorage
from whoosh_modern.storage import CoreStorageAdapter

core = CoreFileStorage("indexdir")
adapter = CoreStorageAdapter(core)

adapter.write("segment_1.dat", b"data")
assert adapter.read("segment_1.dat") == b"data"
assert adapter.exists("segment_1.dat") is True
adapter.delete("segment_1.dat")
```

## AsyncFileStorage

Async variant of `FileStorage`. All operations run on a worker thread via
`asyncio.to_thread` so the event loop is never blocked.

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

## S3Storage

S3-compatible blob storage. `boto3` is imported lazily, so it is an optional
dependency. A `client` can be injected for testing.

```python
from whoosh_modern.storage import S3Storage

# Default client (requires boto3 installed and configured)
storage = S3Storage(bucket="my-index-bucket", prefix="segments")

# Or inject a client for testing / custom configuration
storage = S3Storage(
    bucket="my-index-bucket",
    prefix="segments",
    client=my_boto3_client,
)

storage.write("segment_1.dat", b"data")
data = storage.read("segment_1.dat")
keys = storage.list_keys()
```

Install the optional dependency:

```bash
pip install whoosh-ng[s3]
```

## SnapshotStorage

Simple S3 snapshot storage. S3 remains the source of truth; on read, the object is
downloaded from S3 and also persisted under `local_path` so subsequent reads of the same
key can be served from the local scratch copy:

- Write: upload segment directly to S3
- Read: download segment from S3, cache it under `local_path`

Use this when you want S3 as a simple backup/restore target without the
complexity of a local cache.

```python
from whoosh_modern.storage import SnapshotStorage

storage = SnapshotStorage(
    local_path="./index",
    bucket="my-index-bucket",
    prefix="snapshots",
)

storage.write("segment_1.dat", b"data")
data = storage.read("segment_1.dat")
```

## HybridStorage / CachedObjectStorage

`HybridStorage` composes a local cache and a remote backend. The remote is
the source of truth; the local cache is a write-through performance layer.

`CachedObjectStorage` is an alias for `HybridStorage` that better conveys
the intent: a local object cache synchronized with S3.

This is the recommended architecture for production deployments with repeated
read patterns.

```python
from whoosh_modern.storage import HybridStorage, S3Storage

remote = S3Storage(bucket="my-index-bucket", prefix="segments")
storage = HybridStorage(local_cache="./cache", remote=remote)

# Write-through: remote is source of truth, cache is updated on success
storage.write("segment_1.dat", b"data")

# First read: cache miss → fetch from S3, write-through into cache
data = storage.read("segment_1.dat")

# Second read: cache hit → served from local disk, zero network
data = storage.read("segment_1.dat")

# Force refresh from remote
storage.invalidate("segment_1.dat")

# Warm cache proactively
storage.prefetch(["segment_2.dat", "segment_3.dat"])
```

### Read path

1. local cache hit → return immediately
2. cache miss → read from remote, write-through into cache, return

### Write path

- `remote.write(key, data)` (source of truth)
- on success → `local_cache.write(key, data)`
- on failure → raise before polluting cache

### Cache eviction

The local cache is bounded by `max_cache_size_mb` (default 1024 MB). When
the limit is reached, the oldest entries are evicted using an LRU policy.

### `list_keys`

`list_keys()` uses the remote as source of truth because the cache is only
partial. Pass `include_cache=True` to return the union of remote and cache
keys.

## AsyncHybridStorage

Async variant of `HybridStorage`. Remote operations are executed on a worker
thread via `asyncio.to_thread` so the event loop is never blocked.

```python
import asyncio
from whoosh_modern.storage import AsyncHybridStorage, S3Storage

remote = S3Storage(bucket="my-index-bucket", prefix="segments")
storage = AsyncHybridStorage(local_cache="./cache", remote=remote)

async def main() -> None:
    await storage.awrite("segment_1.dat", b"data")
    data = await storage.aread("segment_1.dat")
    await storage.adelete("segment_1.dat")
    keys = await storage.alist_keys()

asyncio.run(main())
```

## Performance Benchmarks

Benchmarks were run against a local MinIO instance using a 28.89 MB Whoosh
index (2 segment files). Results are indicative of relative performance
between strategies on S3-compatible storage.

| Strategy | Backup (MB/s) | Restore (MB/s) | Notes |
|----------|---------------|----------------|-------|
| `1_obj_per_segment` | 39.44 | 139.72 | Best restore throughput; simplest |
| `compressed_zstd` | 31.56 | 133.74 | Lower bandwidth, CPU overhead |
| `hybrid_cache_s3` | 44.97 | 133.61 | Best backup; excellent warm-cache reads |
| `1_obj_per_posting_list` | 0.28 | 4.79 | **Avoid**: millions of small objects kill S3 |

### Recommendations

- **Default**: `S3Storage` with 1 object per segment file. It offers the
  best restore throughput and is the simplest to operate.
- **Production with repeated reads**: `HybridStorage(local_cache, S3Storage)`.
  After the first read, subsequent reads are served from local disk at
  ~133 MB/s.
- **Avoid**: 1 object per posting list. S3 is not optimized for millions of
  tiny objects; latency and cost explode.
- **Compression**: ZSTD reduces transfer size by ~20-30% at the cost of CPU.
  Use it when network bandwidth is the bottleneck, not when CPU is.

### Running the benchmarks

```bash
# Start MinIO
docker run -d --name minio-benchmark -p 9000:9000 -p 9001:9001 \
  -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
  minio/minio:latest server /data --console-address ":9001"

# Run synthetic benchmark
python benchmark/s3_storage_benchmark.py

# Run real Whoosh index benchmark (requires customers CSV)
python benchmark/s3_storage_benchmark_real.py
```

## How Storage Providers Integrate into the Indexing and Search Pipeline

The storage provider participates in two distinct phases: **index creation** (determining where segments live) and **runtime pipeline integration** (via `StorageMiddleware`).

### Full indexing flow with a storage provider

```text
DataSource.stream_batches()
    │
    ▼
SearchApplication.build()
    │
    ├── source.discover_schema() ──► Whoosh Schema
    │
    ├── storage root resolution
    │       │
    │       ├── FileStorageProvider (exposed as `FileStorage`)
    │       │   └── exposes a public `root` ──► whoosh.index.create_in(root, schema)
    │       │
    │       └── Other providers (S3 / Snapshot / Hybrid, no filesystem root)
    │           └── tempfile.mkdtemp() ──► create_in(tmpdir, schema)
    │
    ├── Writer = index.writer()
    │       │
    │       ├── MiddlewareChain.before_index()
    │       │   └── StorageMiddleware.before_index()
    │       │       ├── context.labels["storage_backend"] = provider.__class__.__name__
    │       │       └── context.metadata["storage_provider"] = self
    │       │
    │       ├── for batch in source.stream_batches():
    │       │       for doc in batch:
    │       │           writer.add_document(**doc)
    │       │
    │       └── writer.commit()
    │           │
    │           └── StorageMiddleware.on_commit()
    │               └── provider.write("commits/{name}/{timestamp}", b"1")
    │
    ▼
Index persisted on disk / S3 / hybrid cache
```

### Full search flow with a storage provider

```text
SearchApplication.search(query)
    │
    ├── index.searcher()
    │       │
    │       └── Whoosh core opens segment files from:
    │           ├── local filesystem (FileStorageProvider root)
    │           ├── SQLite DB (SQLiteStorageProvider)
    │           └── S3 / hybrid cache (S3StorageProvider / HybridStorage)
    │
    ├── QueryParser.parse(query) ──► Query object
    │
    └── searcher.search(query)
        │
        └── Whoosh core reads posting lists from segment files
            └── Returns Results (Hits)
```

### StorageMiddleware hooks in detail

`StorageMiddleware` (`whoosh_modern.middleware.storage`) is the integration point
that routes index persistence through any `SyncStorageProvider` without modifying
the writer.

| Hook | When | What it does |
|------|------|--------------|
| `before_index(context)` | Before each document is added | Tags the context with `storage_backend` label and `storage_provider` metadata |
| `on_commit(context)` | After `writer.commit()` | Writes a commit checkpoint marker (`commits/{name}/{timestamp}`) to the provider |

### Example: StorageMiddleware with a custom chain

```python
from whoosh_modern.middleware import (
    StorageMiddleware,
    FileStorageProvider,
    StemmingMiddleware,
)
from whoosh.middleware.chain import MiddlewareChain
from whoosh_modern.analysis import get_stemmer

# Storage provider
storage = FileStorageProvider("/data/index")

# Create middleware chain
chain = MiddlewareChain([
    StorageMiddleware(storage, name="primary"),
    StemmingMiddleware(stemmer=get_stemmer("auto", "english").stem),
])

# Apply to writer
from whoosh.middleware.wrappers import MiddlewareWriter

with MiddlewareWriter(ix.writer(), chain) as writer:
    writer.add_document(title="Hello", content="World")
    # StorageMiddleware.before_index() tags the context
    # StemmingMiddleware stems the fields
    # writer.commit() triggers StorageMiddleware.on_commit()
    writer.commit()
```

### Key insight: StorageProvider vs StorageMiddleware

| Component | Role |
|-----------|------|
| `SyncStorageProvider` / `AsyncStorageProvider` | **Contract** defining `write()`, `read()`, `delete()`, `exists()`, `list_keys()` |
| `FileStorageProvider`, `S3StorageProvider`, `HybridStorage` | **Implementations** of the contract |
| `StorageMiddleware` | **Integration layer** that calls the provider at specific lifecycle hooks (`before_index`, `on_commit`) |
| `SearchApplication` | **Entry point** that delegates to `SearchView.build()`; resolves the index path from `FileStorageProvider.root` or a temporary directory. See [SearchApplication](/modern/search-application). |

The provider itself does **not** intercept Whoosh's internal segment reads. Those reads go through Whoosh's built-in `FileStorage` (`whoosh.filedb.filestore`) which reads from the filesystem path given to `create_in()`. The Whoosh-NG storage provider abstraction is designed for:
- Custom segment routing (S3, SQLite, hybrid cache)
- Commit checkpointing via middleware
- Future: segment-level read/write interception

## See Also

- [Provider Integration Guide](provider-integration.md) — Complete pipeline guide for all providers
- [Middleware Guide](middleware-pipeline.md) — Pipeline hooks and provider adapters
