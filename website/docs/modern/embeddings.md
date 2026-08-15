---
title: "Embeddings"
sidebar_position: 70
---

# Embeddings

Whoosh-NG can embed documents into dense vectors and use them for semantic
search. This page covers the full embeddings stack: **FastEmbedProvider**
(default CPU backend), **ONNXEmbeddingProvider** (advanced CPU backend),
**EmbeddingModelRegistry**, **EmbeddingModelManager**, the
`whoosh-ng-models` CLI, and `EmbeddingEngine` for `ConfigEngine` integration.

> **Module:** `whoosh_modern.embeddings`
> **Version:** 3.1.0

## Install

```bash
# Default CPU backend (FastEmbed)
pip install whoosh-ng[embeddings]

# Advanced CPU backend (ONNX Runtime)
pip install whoosh-ng[embeddings-onnx]

# Sentence-transformers backend
pip install whoosh-ng[embeddings-sentence-transformers]

# Full stack with vector search
pip install whoosh-ng[embeddings,vector]
```

## Quickstart

```python
from whoosh_modern.embeddings import FastEmbedProvider

provider = FastEmbedProvider()
vector = provider.embed("hello world")
print(len(vector))  # 384

batch = provider.embed_batch(["hello", "world"])
print(len(batch))   # 2
```

## Providers

### FastEmbedProvider (default)

`FastEmbedProvider` is the default CPU-friendly backend. It wraps
`fastembed.TextEmbedding`, which downloads and caches models automatically.

```python
from whoosh_modern.embeddings import FastEmbedProvider

provider = FastEmbedProvider()
# Or with a custom model:
provider = FastEmbedProvider(model_name="BAAI/bge-base-en-v1.5")
```

- Zero PyTorch dependency.
- CPU-only.
- Automatic model download and caching.
- Conforms to `EmbeddingProvider`.

### ONNXEmbeddingProvider (advanced)

`ONNXEmbeddingProvider` wraps an ONNX model and a HuggingFace `tokenizers`
tokenizer. It handles tokenization, inference, pooling, and optional L2
normalization.

ONNX models can be obtained in two ways:

**Option A — via EmbeddingModelManager (recommended for registered models):**

The `EmbeddingModelManager` downloads and caches ONNX models from the
HuggingFace Hub into `~/.whoosh-ng/models/`. Once a model is installed, you
pass the local directory path to the provider:

```python
from whoosh_modern.embeddings import EmbeddingModelManager, ONNXEmbeddingProvider

# Download the model (one-time; cached afterwards)
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
```

**Option B — via explicit local paths (already downloaded or custom models):**

```python
from whoosh_modern.embeddings import ONNXEmbeddingProvider

provider = ONNXEmbeddingProvider(
    model_path="models/multilingual-e5-small/model.onnx",
    tokenizer_dir="models/multilingual-e5-small",
    pooling="mean",
    normalize=True,
)
```

#### Constructor arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `model_path` | `str` | required | Path to the `.onnx` model file |
| `tokenizer_dir` | `str \| None` | parent of `model_path` | Directory containing `tokenizer.json` |
| `pooling` | `str` | `"mean"` | One of `"mean"`, `"cls"`, `"max"` |
| `normalize` | `bool` | `True` | L2-normalize output vectors |
| `dimension` | `int \| None` | `None` | Expected embedding dimension (inferred from model if omitted) |
| `enable_prefix` | `bool` | `True` | Prepend E5-style `"passage: "` / `"query: "` prefix |

#### Pooling strategies

| Strategy | Description |
|----------|-------------|
| `mean` | Average of all real-token embeddings (mask-aware) |
| `cls` | First token embedding |
| `max` | Element-wise maximum over real tokens |

#### E5-style task prefixes

When `enable_prefix=True`, `embed()` prepends `"passage: "` and
`embed_batch(..., is_query=True)` prepends `"query: "`. Set
`enable_prefix=False` when the model does not expect a prefix.

## Provider Model Naming: FastEmbed vs ONNX

The two providers interpret model identifiers differently. Understanding
this distinction avoids confusion with names that exist in both registries:

| Aspect | FastEmbedProvider | ONNXEmbeddingProvider |
|--------|-------------------|-----------------------|
| Identifier type | HuggingFace model name (e.g. `BAAI/bge-small-en-v1.5`) | Registered model name (e.g. `bge-small-en-v1.5`) **or** a local file path |
| Download mechanism | `fastembed` downloads automatically on first use | `EmbeddingModelManager.download()` downloads from the Hub |
| Cache location | FastEmbed's own cache (`~/.cache/fastembed`) | `~/.whoosh-ng/models/` |
| Registry | None (FastEmbed manages its own model list) | `EmbeddingModelRegistry` (`get_default_registry()`) |
| Example | `FastEmbedProvider(model_name="BAAI/bge-small-en-v1.5")` | `ONNXEmbeddingProvider(model_path=str(model_dir / "model.onnx"))` |

> **Ambiguity note:** The name `bge-small-en-v1.5` exists both as a
> FastEmbed model (a HuggingFace repo identifier without namespace) and as
> an ONNX registry entry. They produce similar embeddings but are **not
> interchangeable** — FastEmbed manages its own download, while the ONNX
> registry maps to `onnx-community/bge-small-en-v1.5-ONNX` via
> `EmbeddingModelManager`.

## Model manager and registry

### EmbeddingModelRegistry

`EmbeddingModelRegistry` stores `ModelInfo` metadata for known ONNX models.

```python
from whoosh_modern.embeddings import get_default_registry

registry = get_default_registry()
info = registry.resolve("multilingual-e5-small")
print(info.dimension)   # 384
print(info.pooling)     # mean
print(info.normalize)   # True
```

Pre-registered models:

| Name | Dimension | Pooling | Description |
|------|-----------|---------|-------------|
| `bge-small-en-v1.5` | 384 | mean | English BGE-small (ONNX) |
| `multilingual-e5-small` | 384 | mean | Multilingual E5-small |
| `mini-lm-en-ONNX` | 384 | cls | MiniLM English |
| `bge-small-en-v1.5-int8` | 384 | mean | BGE-small INT8 quantized |

### EmbeddingModelManager

`EmbeddingModelManager` downloads and caches ONNX models locally under
`~/.whoosh-ng/models/` (override with `WHOOSH_NG_MODELS_DIR`).

```python
from whoosh_modern.embeddings import EmbeddingModelManager

manager = EmbeddingModelManager()

# Download a model from HuggingFace
model_dir = manager.download("multilingual-e5-small")

# Check if installed
print(manager.is_installed("multilingual-e5-small"))  # True

# List installed models
print(manager.list_installed())

# Verify checksum
print(manager.verify_checksum("multilingual-e5-small", "sha256hex..."))

# Remove
manager.remove("multilingual-e5-small")
```

## CLI

A console script `whoosh-ng-models` is installed with the `embeddings-onnx`
extra:

```bash
whoosh-ng-models list
whoosh-ng-models list --all
whoosh-ng-models info multilingual-e5-small
whoosh-ng-models install multilingual-e5-small
whoosh-ng-models verify multilingual-e5-small --expected-sha256 <hex>
whoosh-ng-models remove multilingual-e5-small
whoosh-ng-models update multilingual-e5-small
```

Use `--models-dir` to override the default models directory.

Use `--hf-token` to authenticate with the HuggingFace Hub. It falls back to
`HF_TOKEN` / `HUGGING_FACE_HUB_TOKEN` environment variables. Public models
work without a token, but authenticated requests get higher rate limits and
faster downloads.

## ConfigEngine integration

`EmbeddingEngine` (`whoosh_modern.config.engines.embedding.EmbeddingEngine`) reads the
`embedding` block from `WhooshNGConfig` and instantiates the matching provider.

```yaml
# whoosh-ng.yml
embedding:
  provider: fastembed
  model: BAAI/bge-small-en-v1.5
```

```yaml
# ONNX with a registered model name
# EmbeddingModelManager downloads and caches the model automatically,
# deriving model_path and tokenizer_dir from the local cache.
embedding:
  provider: onnx
  model: multilingual-e5-small
  pooling: mean
  normalize: true
```

```yaml
# ONNX with explicit local paths (custom or pre-downloaded models)
embedding:
  provider: onnx
  model_path: models/multilingual-e5-small/model.onnx
  tokenizer_dir: models/multilingual-e5-small
  pooling: mean
  normalize: true
```

```yaml
# sentence-transformers
embedding:
  provider: sentence-transformers
  model: all-MiniLM-L6-v2
```

```yaml
# Multi-field vectorization
# When embedding_fields is used, omit source_field/target_field at the
# root level — they are ignored when embedding_fields is present.
embedding:
  provider: fastembed
  model: BAAI/bge-small-en-v1.5
  embedding_fields:
    - source_field: title
      target_field: title_vector
    - source_field: body
      target_field: body_vector
```

Supported providers: `fastembed`, `onnx`, `sentence-transformers`.

> **Multi-field precedence:** When `embedding_fields` is provided, the
> root-level `source_field` / `target_field` defaults are **ignored** — each
> entry in `embedding_fields` is processed independently. The
> `SearchView` automatically injects the target fields as `VECTOR` fields
> into the generated Whoosh schema if they are not already declared. To
> avoid confusion, omit `source_field` and `target_field` from the root
> level when using `embedding_fields`.

### ONNX configuration

When using `provider: onnx`, you can specify a registered model via `model`
or provide explicit file paths via `model_path` and `tokenizer_dir`.

- If `model` is specified, `EmbeddingModelManager` will download and manage
  the model, automatically deriving `model_path` and `tokenizer_dir` from the
  local cache.
- If `model_path` and/or `tokenizer_dir` are explicitly provided, they take
  precedence over paths derived from the `model` name.

It is recommended to use either `model` for manager-managed models, or
`model_path` / `tokenizer_dir` for custom local paths, to avoid ambiguity.

## Error Handling

> **Design decision:** Provider errors are **swallowed** (logged as warnings)
> to avoid breaking the indexing pipeline. This applies to all embedding
> providers (FastEmbed, ONNX, Sentence Transformers).

When an embedding provider raises an exception during `embed()` or
`embed_batch()`, the `EmbeddingMiddleware` catches the exception, logs a
warning, and continues indexing. The affected document will be indexed
**without** its vector field, meaning it will not be searchable via semantic
(similarity) search but remains searchable via keyword (BM25) matching.

The relevant Python `logging` logger names are:

| Logger | Source module |
|--------|---------------|
| `whoosh_modern.middleware.embedding` | `EmbeddingMiddleware.before_index()` |
| `whoosh_modern.config.engines.embedding` | `EmbeddingEngine.build()` |

Configure logging to control verbosity and destination:

```python
import logging

# Log embedding warnings to a dedicated file
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename="embedding_warnings.log",
)

# Or raise warnings to ERROR so they surface during development
logging.getLogger("whoosh_modern.middleware.embedding").setLevel(logging.ERROR)
```

### Benchmark error handling

The benchmark script `benchmark/stock_parquet_embedding.py` follows the same
pattern: provider exceptions are caught, a warning is printed to `stderr`,
and the document is skipped. Tracked failures are reported in the benchmark
output under the `failures` key.

## Protocol

Any object that implements `embed(text: str) -> Sequence[float]` satisfies
the `EmbeddingProvider` protocol (`whoosh_modern.embeddings.protocol`).

```python
from whoosh_modern.embeddings.protocol import EmbeddingProvider

class MyProvider:
    def embed(self, text: str) -> list[float]: ...
```

## Examples

- [Embeddings with FastEmbed](/examples/embeddings-fastembed) — Runnable FastEmbed example
- [Embeddings with ONNX](/examples/embeddings-onnx) — Runnable ONNX example

## See Also

- [Vector Search](/modern/vector) — Using embeddings for semantic search
- [Storage Providers](/modern/storage-providers) — Persisting vector indexes
- [Configuration Engine](/modern/configuration-engine) — Typed configuration surface
