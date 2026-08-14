# Changelog

All notable changes to Whoosh-NG are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.1.0] - Unreleased

### Added

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

**[Autres]**
- **Documentation** (`website/docs/modern/synonyms.md`): added Wiktionary
  Indexing Integration section covering `import_wiktionary_index()`,
  `SearchApplication` integration, and middleware wiring.

### Breaking Changes

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

### In Progress (tracked in `.kilo/plans/1786003980063-whoosh-ng-roadmap.md`)
- Sprint F: Admin Studio (NiceGUI) + Synonym Manager remain.

[5.1.0]: https://github.com/dorel14/whoosh-NG/releases/tag/v5.1.0
