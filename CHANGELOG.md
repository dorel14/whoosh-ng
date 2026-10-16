# Changelog

All notable changes to Whoosh-NG are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.1.0] - Unreleased

### Added

**[Embeddings]**
- **LibEmbeddingProvider** (`src/whoosh_modern/embeddings/libembedding_provider.py`):
  New embedding provider backed by `libembedding-ng` (CPU-only, zero PyTorch,
  ~2x faster than FastEmbed). Supports `"fast"`, `"balanced"`, `"quality"` presets
  via `TextEmbedding.from_mode()` with automatic model selection.
- **ProviderPool** (`src/whoosh_modern/embeddings/provider_pool.py`):
  Thread-safe pool of embedding provider instances for parallel inference.
  Distributes `embed_batch()` calls round-robin across N instances with
  `ThreadPoolExecutor` for true parallelism (+150% throughput vs single provider).
- **EmbeddingBatchWriter** (`src/whoosh_modern/indexing/embedding_writer.py`):
  High-performance batch writer with provider pooling, thread-safe LRU cache,
  persistent NPZ disk cache, strict error handling, dimension validation,
  and in-place document mutation (-40% memory, -17% dict copy overhead).
- **EmbeddingMiddleware v4** (`src/whoosh_modern/middleware/embedding.py`):
  Batch accumulation mode (+33% throughput via `embed_batch()`), fixed
  document return queue (all batch docs now indexed, not just first),
  strict mode, and `on_commit()` flush.
- **Model preloading** (`src/whoosh_modern/embeddings/model_preload.py`):
  `preload_embedding_model_async()` / `preload_embedding_model()` for
  async/sync warmup at startup; `preload_embedding_provider_pool()` for pools.
- **Persistent embedding cache** (`src/whoosh_modern/embeddings/embedding_cache.py`):
  NPZ-format on-disk cache for cross-run embedding reuse.
- **ONNXEmbeddingProvider enhancements**: CUDAExecutionProvider support with
  correct provider ordering (GPU tried first), configurable intra/inter-op
  threads, graph optimization levels, and quantization presets.
- **FastEmbedProvider enhancements**: `"fast"` preset auto-selects best
  available model (384-dim preferred), native `parallel`/`batch_size`/
  `lazy_load` params, thread count via constructor (no global env mutation).

**[Wiktionary]**
- **Wiktionary synonym provider** (`src/whoosh_modern/linguistics/synonyms/wiktionary_provider.py`):
  `WiktionarySynonymProvider` loads large-scale multilingual synonym dictionaries
  from kaikki.org JSON Lines files, with POS filtering and space-in-word
  exclusion.
- **Wiktionary dictionary update script** (`scripts/update_wiktionary_dictionaries.py`):
  downloads `kaikki.org-dictionary-all.jsonl`, extracts synonyms by language, and
  writes compact per-language JSON Lines files into
  `src/whoosh_modern/linguistics/dictionaries/wiktionary/`.
- **Pre-generated dictionaries**: `fr.json`, `en.json`, `de.json`, `es.json`,
  `it.json` sample dictionaries and `manifest.json` for the Wiktionary provider.
- **SynonymManager.import_wiktionary()**: import synonyms from a Wiktionary
  JSON Lines dictionary file via `SynonymManager.import_wiktionary(path)`.
- **Wiktionary dictionary indexer** (`src/whoosh_modern/linguistics/wiktionary_indexer.py`):
  `WiktionaryIndexer` builds a Whoosh-NG full-text index from any `DataSource`
  (e.g. `JSONSource`), with a fixed schema exposing `word`, `definition`,
  `synonyms`, `antonyms`, `forms`, `pos`, and `language` fields, plus
  `build_index(source, language)` and `search(query, language, limit)`.
- **SynonymManager.import_wiktionary_index**, `SearchApplication` integration:
  `SynonymManager` can now import synonyms from a built `WiktionaryIndexer`,
  and `SearchApplication` exposes a lazily populated `synonym_manager`
  property when a `WiktionaryIndexer` is provided, ready for
  `SynonymExpansionMiddleware` wiring.
- **Extended dictionary format**: `update_wiktionary_dictionaries.py` writes
  `definition`, `n` (antonyms), and `forms` alongside synonyms, producing
  richer JSON Lines dictionaries for the indexer.
- **Updated sample dictionaries**: `fr.json`, `en.json`, `de.json`, `es.json`,
  `it.json` now include definitions, antonyms, and forms.
- **Documentation** (`website/docs/modern/synonyms.md`): dedicated synonyms guide
  covering all providers, the Wiktionary update workflow, and integration examples.
- **Tests** (`tests/linguistics/test_wiktionary_indexer.py`): 5 tests covering
  build+search, language filtering, metadata returned, empty results, and
  all-languages indexing.

**[Langue & Multilingue]**
- **Language Auto-Detection** (`whoosh_modern.linguistics.detection`):
  `StopwordDetector` and `LangDetectProvider` for automatic language detection
  with configurable supported languages.
- **Language Registry** (`whoosh_modern.linguistics.registry`):
  `LanguageRegistry`, `StemmerRegistry`, and `LanguageProfile` for centralized
  language/analyzer/stemmer resolution with `get_default_registry()`.
- **Multi-Language Analyzer** (`whoosh_modern.linguistics.analyzers`):
  `MultiLanguageAnalyzer` applies multiple language analyzers simultaneously
  for multilingual indexing.
- **Analyzer Presets** (`whoosh_modern.analysis.stemmer_presets`):
  `AnalyzerPresets.documentation()`, `.ecommerce()`, `.blog()`, `.multilingual()`
  for common search scenarios.
- **Explain Analyzer** (`whoosh_modern.linguistics.explain`):
  `ExplainAnalyzer`, `AnalysisExplanation`, and `TokenExplanation` expose the
  tokenization/stemming pipeline for Search Studio visualization.
- **Cached Stemming Analyzer** (`whoosh_modern.analysis.cached_stemming_analyzer`):
  `CachedStemmingAnalyzer` wraps language analyzers with LRU caching
  (`cache_size=50000`) for repeated tokens.
- **Dictionary Stem Override** (`whoosh_modern.linguistics.dictionary_stem_override`):
  `DictionaryStemOverride` allows overriding Snowball stemming with business
  dictionaries (JSON/Wiktionary).
- **Stemmer Profiler** (`whoosh_modern.profiling.stemmer_profiler`):
  `StemmerProfiler` and `StemmerProfilerReport` measure vocabulary reduction,
  estimated index size reduction, and average stemming time per token.
- **Multilingual SearchApplication** (`whoosh_modern.application`):
  `SearchApplication` now accepts `language_detector` and
  `dictionary_stem_overrides` parameters; `FieldConfig` supports `language="auto"`
  with detector resolution.
- **Searcher Configuration** (`whoosh_modern.config`):
  `SearchConfig` now includes a `searcher` block with `SearcherConfig(weighting)`,
  `SearcherEngine` builds it from config, and `SearchApplication` accepts a
  `searcher` parameter used in `search()` to open the index with the configured
  weighting model (`BM25F`, `BM25`, `TF_IDF`, `PL2`, `DFree`, `Frequency`).
- **Embedding Performance v4.0** (`whoosh_modern.embeddings`,
  `whoosh_modern.indexing`, `whoosh_modern.vector`):
  - **FastEmbedProvider**: added `"fast"` preset for automatic selection of the
    fastest available model (`bge-small-en-v1.5` or `snowflake-arctic-embed-s`);
    added `threads` parameter to tune ONNX Runtime thread count via
    `OMP_NUM_THREADS`/`ORT_NUM_THREADS`; added model presets for multilingual
    (`paraphrase-multilingual-MiniLM-L12-v2`) and other variants.
  - **ProviderPool** (`whoosh_modern.embeddings.provider_pool`): thread-safe pool
    of embedding provider instances with round-robin distribution and
    `ThreadPoolExecutor`-based parallel `embed_batch()` across provider instances.
  - **EmbeddingBatchWriter v4.0** (`whoosh_modern.indexing.embedding_writer`):
    thread-safe LRU cache (`ThreadSafeLRUCache`), strict error handling
    (`strict_errors=True`), dimension validation, in-place document mutation,
    batch deduplication, and performance metrics via `get_stats()`.
  - **EmbeddingMiddleware v4.0** (`whoosh_modern.middleware.embedding`):
    batch accumulation mode with configurable `batch_size` (default 32) that
    calls `embed_batch()` instead of per-document `embed()` for +33% throughput.
  - **ONNXEmbeddingProvider**: added `use_cuda=True` for automatic CUDA detection
    with CPU fallback; added `intra_op_num_threads`, `inter_op_num_threads`,
    and `graph_optimization_level` for runtime tuning.
  - **NumpyProvider v4.0** (`whoosh_modern.vector.numpy_provider`): vectorized
    cosine similarity via `matrix @ query` with `np.argpartition` for O(N) top-k
    selection; lazy matrix consolidation; float32 storage for -50% memory usage.
  - **Model preloading** (`whoosh_modern.embeddings.model_preload`):
    `preload_embedding_model_async()` and `preload_embedding_model()` for
    async/sync model warmup at startup.

**[Autres]**
- **Documentation** (`website/docs/modern/synonyms.md`): added Wiktionary
  Indexing Integration section covering `import_wiktionary_index()`,
  `SearchApplication` integration, and middleware wiring.

### Breaking Changes

- **Default embedding provider changed**: The default embedding provider in
  `EmbeddingConfig` is now `"libembedding"` (requires `libembedding-ng` extra).
  Previously it was `None` (no embedding by default). To use FastEmbed or
  ONNX instead, explicitly set `provider: "fastembed"` or `provider: "onnx"`
  in your embedding configuration. The `embeddings` extra no longer includes
  `sentence-transformers` (PyTorch dependency); use `embeddings-sentence-transformers`
  extra if needed.

- **Import path change**: The project was renamed from `whoosh-reloaded` to
  `whoosh-ng`. The modern extension modules previously available under
  `whoosh_reloaded` are now importable under `whoosh_modern`. Existing code
  using `whoosh_reloaded` must be updated to `whoosh_modern`. Core Whoosh
  components remain available under the `whoosh` namespace.

### Changed

- **Distribution renamed**: From `whoosh-reloaded` to **`whoosh-ng`**.
- **Configuration Engine** (`src/whoosh_modern/config/engines.py`): added
  sub-engines `SchemaEngine`, `AnalyzerEngine`, `DataSourceEngine`,
  `StorageEngine`, `SearchModelEngine`, `FacetEngine`, `PluginEngine`, and
  `APIEngine` to build concrete Whoosh-NG components from a merged
  `WhooshNGConfig`.
- **Vector Search** (`src/whoosh_modern/vector/`): added `HnswlibProvider` for
  HNSW approximate nearest neighbor search, complementing the existing
  `NumpyProvider`.
- **Embedding Framework** (`src/whoosh_modern/embeddings/`): added
  `EmbeddingProvider` protocol, `SentenceTransformersProvider`,
  `FastEmbedProvider` (default CPU backend via `fastembed`),
  `ONNXEmbeddingProvider` (CPU-friendly, zero PyTorch dependency),
  `EmbeddingModelRegistry` with pre-registered ONNX models,
  `EmbeddingModelManager` for download/cache/checksum verification in
  `~/.whoosh-ng/models/`, the `whoosh-ng-models` CLI
  (`list|install|info|verify|remove|update`), and `EmbeddingEngine`
  (`src/whoosh_modern/config/engines/embedding.py`) for `ConfigEngine`
  integration (`embedding:` YAML/JSON block).
- **Embeddings documentation** (`website/docs/modern/embeddings.md`):
  dedicated guide covering FastEmbed, ONNX, model manager/registry, CLI,
  ConfigEngine integration, protocol, and runnable example.
- **Modern N-Gram Framework** (`src/whoosh_modern/analysis/`): added
  `AutoCompleteAnalyzer`, `EdgeNgramAnalyzer`, `SEARCH_AS_YOU_TYPE` field
  type, and new `AnalyzerPresets` (autocomplete, partial_match, fuzzy,
  code_search, documentation, ecommerce, blog, multilingual).
- **N-Gram Profiler** (`src/whoosh_modern/profiling/ngram_profiler.py`):
  added `NgramProfiler` and `NgramProfilerReport` for measuring n-gram
  generation performance.
- **FastAPI WebSocket autocomplete**: added persistent
  `WS /api/v1/autocomplete/ws` endpoint accepting `{"q":"..."}` messages
  and returning `{"suggestions":[...]}`.
- **CoreStorageAdapter** (`src/whoosh_modern/storage/core_adapter.py`): bridges
  core `whoosh.filedb.filestore.FileStorage` to the modern `SyncStorageProvider`
  interface, exported from `whoosh_modern.storage`.
- **Documentation site** moved to GitHub Pages: https://dorel14.github.io/Whoosh-NG/
- **Required Python version** is now `>=3.11`.
- **Packaging cleaned**: removed redundant `requirements*.txt`; consolidated extras
  (`dev`, `docs`, `metrics`, `vector`, `admin`, `linguistics`).

### Fixed

- **SnapshotStorage regression**: removed duplicated `_safe_local_path()` call
  and redundant S3 read in `SnapshotStorage.read()` that caused path-traversal
  validation to execute twice and the remote object to be fetched twice per read.
- **BatchAnalyzer docstring**: corrected to reflect that the cache stores
  filtered documents, not analysis results.
- **Exception hierarchy**: `DataSourceError` now inherits from `WhooshError`
  (`src/whoosh/__init__.py`), providing a common root for core and modern errors.
- **ModernIndexBuilder**: unused `merge_policy` parameter is now wired to
  `writer.commit(mergetype=...)` in `_build_parallel()`.
- **EmbeddingEngine ONNX model resolution** (`src/whoosh_modern/config/engines/embedding.py`):
  When `provider: onnx` is configured with `model` (a registered model name) but
  no `model_path`, the engine now uses `EmbeddingModelManager` to download and
  cache the model, then derives `model_path` and `tokenizer_dir` from the local
  cache. Previously the model name was incorrectly passed as `model_path`, which
  would fail because `ONNXEmbeddingProvider` expects an actual file path.
  Explicit `model_path` / `tokenizer_dir` still take precedence when provided.
  Added `expected_sha256` field to `EmbeddingConfig` for checksum verification
  during model download.

### Changed

- **Embeddings documentation** (`website/docs/modern/embeddings.md`,
  `website/i18n/fr/docusaurus-plugin-content-docs/current/modern/embeddings.md`):
  - Added `Provider Model Naming` section clarifying that `FastEmbedProvider`
    uses HuggingFace model names auto-downloaded by `fastembed`, while
    `ONNXEmbeddingProvider` uses registered model names downloaded via
    `EmbeddingModelManager` or explicit local file paths.
  - Updated ONNX example to use `EmbeddingModelManager.download()` instead of
    raw file paths.
  - Updated Multi-field vectorization YAML example to omit root-level
    `source_field` / `target_field` when `embedding_fields` is present, with a
    clear precedence note.
  - Moved provider error handling documentation from "Notes" to a dedicated
    `Error Handling` section covering logging configuration and the design
    rationale.
- **Embedding examples** (`website/docs/examples/embeddings-fastembed.md`,
  `website/docs/examples/embeddings-onnx.md`): Updated to reflect the
  `EmbeddingModelManager` workflow for ONNX models and the multi-field
  vectorization precedence rules.
- **EmbeddingMiddleware** (`src/whoosh_modern/middleware/embedding.py`): Improved
  warning log messages to include the source field name and a truncated preview
  of the input text for easier diagnostic. Updated module version to 3.1.0.

### Added

- **LibEmbeddingProvider** (`src/whoosh_modern/embeddings/libembedding_provider.py`):
  new default embedding provider wrapping `libembedding.TextEmbedding` (CPU-only,
  zero PyTorch). Supports presets `"fast"`, `"balanced"`, `"quality"` resolved
  via `TextEmbedding.from_mode()`, plus explicit HF model identifiers.
- **Default provider**: `EmbeddingConfig.provider` now defaults to `"libembedding"`.
- **EmbeddingEngine** (`src/whoosh_modern/config/engines/embedding.py`): added
  `provider_type == "libembedding"` branch with propagation of `model`, `pooling`,
  `batch_size`, `cache_size`.
- **Packaging extras**: added `libembedding = ["libembedding-ng>=1.5"]` and expanded
  `embeddings` extra to include `sentence-transformers` and `libembedding-ng>=1.5`.
- **Examples**: `examples/embeddings_libembedding.py`, `examples/embeddings_onnx.py`.
- **ModelInfo enrichment** (`src/whoosh_modern/embeddings/registry.py`): added
  `size_mb` and `license` fields.

### Changed

- **ONNXEmbeddingProvider** (`src/whoosh_modern/embeddings/onnx_provider.py`):
  `__repr__` now displays `quantization` instead of `pooling`.
- **EmbeddingMiddleware** (`src/whoosh_modern/middleware/embedding.py`): renamed
  `strict_errors` parameter to `strict` to match plan convention.
- **EmbeddingModelManager** (`src/whoosh_modern/embeddings/model_manager.py`):
  direct download URLs now include `?download=true`.

### Fixed

- **EmbeddingEngine ONNX model resolution**: already fixed in 5.1.0.

### In Progress (tracked in `.kilo/plans/1786003980063-whoosh-ng-roadmap.md`)
- Sprint F: Admin Studio (NiceGUI) + Synonym Manager remain.

[5.1.0]: https://github.com/dorel14/whoosh-NG/releases/tag/v5.1.0
