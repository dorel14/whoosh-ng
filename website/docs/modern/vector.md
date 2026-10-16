---
title: "Vector Search"
sidebar_position: 60
---

# Vector Search

Module: `whoosh_modern.vector`
Version: 4.0.0

Whoosh-NG supports semantic search through vector embeddings. This guide covers the vector providers and how to use them with the current API.

## Concept

Vector search lets you find documents based on semantic similarity rather than exact keyword matches. You embed documents and queries into a high-dimensional space, then find nearest neighbors.

```
Query embedding  ----\
                       >--- Cosine Similarity ---> Ranked results
Document embedding ---/
```

## Providers

Whoosh-NG includes two vector backends:

| Provider | Description | Use Case |
|----------|-------------|----------|
| `NumpyProvider` | Pure NumPy, vectorized cosine similarity | Small to medium indexes (up to ~100k docs) |
| `HnswlibProvider` | HNSW approximate nearest neighbor | Large indexes, fast ANN |

### NumpyProvider (Default)

`NumpyProvider` stores vectors in memory and computes cosine similarity using vectorized NumPy operations. It is the default choice for indexes up to ~100k documents.

```python
from whoosh_modern.vector.numpy_provider import NumpyProvider

provider = NumpyProvider()
provider.add([("doc1", [0.1, 0.2, ...]), ("doc2", [0.4, 0.5, ...])])
hits = provider.search(query_embedding, k=10)
for hit in hits:
    print(hit.doc_id, hit.score)
```

**Optimizations v4.0:**
- Vectorized cosine similarity via `matrix @ query`
- Lazy matrix consolidation (built only at search time)
- `np.argpartition` for O(N) top-k selection
- float32 storage for -50% memory usage

### HnswlibProvider

`HnswlibProvider` uses HNSW for approximate nearest neighbor search. Suitable for large indexes where exact search is too slow.

```python
from whoosh_modern.vector.hnswlib_provider import HnswlibProvider

provider = HnswlibProvider(dimension=384, space="cosine")
provider.add([("doc1", [0.1, 0.2, ...]), ("doc2", [0.4, 0.5, ...])])
hits = provider.search(query_embedding, k=10)
```

## Vector Field

Use `VECTOR` from `whoosh_modern.fields` to declare a dense vector field:

```python
from whoosh.fields import Schema, TEXT, ID
from whoosh_modern.fields import VECTOR

schema = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    content=TEXT,
    embedding=VECTOR(dimension=384),
)
```

## Indexing with Vectors

### Generate Embeddings

```python
from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider

provider = FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")
texts = ["First document content", "Second document content"]
embeddings = provider.embed_batch(texts)
```

### Write Documents

```python
with ix.writer() as writer:
    for doc_id, text, embedding in zip(doc_ids, texts, embeddings):
        writer.add_document(
            id=doc_id,
            content=text,
            embedding=embedding,
        )
    writer.commit()
```

## Searching

### Pure Vector Search

```python
from whoosh_modern.vector.numpy_provider import NumpyProvider

provider = NumpyProvider()
# Populate provider with indexed vectors...
query_embedding = provider.embed("search query")
hits = provider.search(query_embedding, k=10)
```

### Hybrid Search (BM25 + Vector)

```python
from whoosh_modern.searching.hybrid import HybridSearcher

with ix.searcher() as searcher:
    hs = HybridSearcher(searcher, vector_provider, id_field="id")
    results = hs.search(
        "Python programming",
        query_vector=query_embedding,
        method="weighted",
        alpha=0.5,
    )
    for r in results:
        print(r.doc_id, r.score, r.bm25_score, r.vector_score)
```

## Performance

For optimal vector search performance:

- **NumpyProvider**: use for indexes up to ~100k vectors. Vectorized matrix multiplication ensures O(N) search time.
- **HnswlibProvider**: use for larger indexes. HNSW provides O(log N) approximate search.
- **Batch embeddings**: use `embed_batch()` instead of per-document `embed()` for +33% throughput.
- **ProviderPool**: use multiple provider instances for parallel embedding on multi-core CPUs.

## See Also

- [Embeddings](/modern/embeddings) — Embedding providers and configuration
- [Hybrid Search](/modern/search-application) — BM25 + vector fusion
- [Storage Providers](/modern/storage-providers) — Persisting vector indexes
- [Configuration Engine](/modern/configuration-engine) — Typed configuration surface
