---
title: "Storage Providers"
nav_order: 210
---

# Storage Providers

Whoosh-NG provides pluggable storage backends through the
`SyncStorageProvider` / `AsyncStorageProvider` contracts. This allows the
index to be persisted on local disk, SQLite, S3, or a hybrid cache + remote
setup without changing the writer or the index.

## Available providers

| Provider | Type | Backend |
|----------|------|---------|
| `FileStorage` | sync | local filesystem |
| `AsyncFileStorage` | async | local filesystem |
| `S3Storage` | sync | S3-compatible object storage |
| `HybridStorage` | sync | local cache + any remote backend |
| `AsyncHybridStorage` | async | local cache + any remote backend |

All providers are importable from `whoosh_modern.storage`.

## FileStorage

Local filesystem storage. Keys are relative paths under `root`.

```python
from whoosh_modern.storage import FileStorage

storage = FileStorage("indexdir")
storage.write("segment_1.dat", b"binary-data")
assert storage.read("segment_1.dat") == b"binary-data"
assert storage.exists("segment_1.dat") is True
storage.delete("segment_1.dat")
keys = storage.list_keys()
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

## HybridStorage

`HybridStorage` composes a local cache and a remote backend. The remote is
the source of truth; the local cache is a write-through performance layer.

This is the key differentiator of Whoosh-NG for large, cloud-native indexes.

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

## Using storage with SearchApplication

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
results = app.index.search("laptop")
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
