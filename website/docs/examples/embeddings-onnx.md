---
title: "Embeddings with ONNX"
sidebar_position: 261
---

# Embeddings with ONNX

This example shows how to use **ONNX** for dense vector embeddings in Whoosh‑NG.

## 1. Install Dependencies

```bash
pip install "whoosh-ng[embeddings-onnx]" onnx
```

## 2. Install a Model (via EmbeddingModelManager)

Before using an ONNX provider, download and cache the model files using the
`EmbeddingModelManager`. This handles downloads from the HuggingFace Hub
and cache management for you:

```python
from whoosh_modern.embeddings import EmbeddingModelManager

manager = EmbeddingModelManager()
model_dir = manager.download("multilingual-e5-small")
print(manager.is_installed("multilingual-e5-small"))  # True
print(sorted(model_dir.glob("*.onnx")))               # [model.onnx]
```

You can also manage models via the CLI:

```bash
whoosh-ng-models install multilingual-e5-small
whoosh-ng-models list
```

## 3. Single-Field Vectorization

```python
from pathlib import Path

from whoosh.fields import Schema, TEXT
from whoosh.index import create_in
from whoosh_modern import SearchApplication
from whoosh_modern.data_sources.in_memory import InMemorySource
from whoosh_modern.embeddings import EmbeddingModelManager, ONNXEmbeddingProvider

# Download the model (skipped if already cached)
manager = EmbeddingModelManager()
model_dir = manager.download("multilingual-e5-small")

# Resolve the .onnx file path
onnx_path = str(next(model_dir.glob("*.onnx")))

provider = ONNXEmbeddingProvider(
    model_path=onnx_path,
    tokenizer_dir=str(model_dir),
    pooling="mean",
    normalize=True,
)
source = InMemorySource(
    documents=[
        {"title": "Whoosh-NG", "body": "Modern Python full-text search."},
        {"title": "ONNX", "body": "Lightweight model runtime."},
    ],
    schema=Schema(title=TEXT(stored=True), body=TEXT),
)

app = SearchApplication(
    source=source,
    embedding_provider=provider,
    source_field="body",
    target_field="body_vector",
)
app.build("indexdir")
```

## 4. Multi-Field Vectorization

When `embedding_fields` is provided, the root-level `source_field` /
`target_field` defaults are ignored — each mapping is processed
independently. Omit the root-level fields to avoid confusion:

```python
app = SearchApplication(
    source=source,
    embedding_provider=provider,
    embedding_fields=[
        {"source_field": "title", "target_field": "title_vector"},
        {"source_field": "body", "target_field": "body_vector"},
    ],
)
app.build("indexdir")
```

## 5. Inspect Stored Vectors

```python
with app.index.searcher() as searcher:
    for stored in searcher.all_stored_fields():
        print(stored.get("title_vector"))
        print(stored.get("body_vector"))
```

## Notes

- The target vector fields are added to the schema automatically as `VECTOR` fields.
- If a source field is missing or not a string, it is skipped silently.
- Provider errors are swallowed to avoid breaking the indexing pipeline.
  See the [_embeddings guide](/modern/embeddings#error-handling) for logging
  configuration.
