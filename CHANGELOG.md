# Changelog

All notable changes to Whoosh-NG are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0.dev0] - Unreleased

### Added
- **Configuration Engine sub-engines** (`src/whoosh_modern/config/engines.py`):
  `SchemaEngine`, `AnalyzerEngine`, `DataSourceEngine`, `StorageEngine`,
  `SearchModelEngine`, `FacetEngine`, `PluginEngine`, and `APIEngine` to
  build concrete Whoosh-NG components from a merged `WhooshNGConfig`.
- **Plugin System** (`src/whoosh/plugins/`): `Plugin` base class and `PluginManager`
  with entry-point auto-discovery, version validation, conflict detection,
  enable/disable, and dependency management.
- **Registry System** (`src/whoosh/registry/`): generic `Registry` plus
  `StorageRegistry`, `AnalyzerRegistry`, `RankingRegistry`, `SuggestRegistry`,
  `VectorRegistry`, `AutocompleteRegistry`, and `BackendRegistry`.
- **Middleware Pipeline** (`src/whoosh/middleware/`): `Middleware` base class
  (sync + async via `inspect.isawaitable`), `MiddlewareContext`, `MiddlewareChain`,
  `MiddlewareRegistry`, `MiddlewareWriter`/`MiddlewareSearcher` wrappers, and
  official `MetricsMiddleware`, `CacheMiddleware`, `CompressionMiddleware`,
  `EncryptionMiddleware`, and `PrometheusMiddleware`.
- **Event Bus** (`src/whoosh/event_bus.py`): `EventBus` with subscribe/publish/clear.
- **Hook System** (`src/whoosh/hooks.py`): `hookimpl`, `register_hook`, `call_hook`,
  integrated into the plugin lifecycle.
- **Backends** (`src/whoosh/backends/`): `Backend` ABC with lifecycle hooks,
  `FileBackend`, and `SQLiteBackend`.
- **Provider architecture**: `VectorProvider`/`VectorField`
  (`src/whoosh/vector/base.py`), `NumpyProvider` (`src/whoosh_modern/vector/`),
  and `HNSWProvider` (`src/whoosh/providers/hnsw.py`).
- **Autocomplete plugin** (`whoosh_modern.autocomplete`): `AutocompleteProvider`,
  `EdgeNgram`/`InvertedIndexAutocomplete`, registered via entry point.
- **FastAPI plugin** (`whoosh_fastapi`): app factory `create_app` with search,
  autocomplete, vector, and health endpoints.
- **Admin UI plugin** (`whoosh_admin`): dashboard app factory `create_admin_app`.
- **Observability**: `PrometheusMiddleware` exposed via the `metrics` extra.
 - Entry points under `whoosh.plugins` for autocomplete, vector, fastapi,
   observability, and admin.
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
- **Documentation** (`website/docs/modern/synonyms.md`): dedicated synonyms guide
  covering all providers, the Wiktionary update workflow, and integration examples.

### Changed
- Renamed distribution from `whoosh-reloaded` to **`whoosh-ng`**. The import
  namespace remains `whoosh` for backward compatibility.
- Documentation site moved to GitHub Pages: https://dorel14.github.io/Whoosh-NG/
- Required Python version is now `>=3.11`.
- Packaging cleaned: removed redundant `requirements*.txt`; consolidated extras
  in `pyproject.toml`.
- Type annotations modernized: `mypy src/whoosh` reports 0 errors. `py.typed`
  marker shipped.

### Fixed
- **Security**: fixed a path traversal vulnerability in
  `whoosh_modern.storage.s3.SnapshotStorage.read()` where a malicious S3
  object key (e.g. `../../etc/passwd`) could write files outside the
  configured `local_path`. Keys are now sanitized and validated before being
  used to build local scratch file paths, raising `ValueError` for `..`
  segments, absolute paths, or resolutions escaping `local_path`.
- `whoosh_modern.linguistics.stemmers`: restored backward compatibility for
  `FrenchAnalyzer`, `EnglishAnalyzer`, `GermanAnalyzer`, `SpanishAnalyzer`, and
  `ItalianAnalyzer`. These are still ready-to-use `CompositeAnalyzer`
  instances (`FrenchAnalyzer(text)`), but calling them with no arguments
  (`FrenchAnalyzer()`) now returns a fresh analyzer instance instead of
  raising `TypeError`, so historical class-style usage
  (`FrenchAnalyzer()(text)`) keeps working.

### Added
- **Configuration Engine** (`src/whoosh_modern/config/`): `ConfigEngine` with
  hierarchical merging (language → application → instance → runtime), Pydantic
  models (`WhooshNGConfig`, `FieldConfig`, `SearchConfig`, `DataSourceConfigModel`,
  `StorageConfigModel`), and YAML/JSON loaders with validation.
- **FastAPI WebSocket autocomplete**: persistent `WS /api/v1/autocomplete/ws`
  endpoint accepting `{"q":"..."}` messages and returning `{"suggestions":[...]}`.
- **CoreStorageAdapter** (`src/whoosh_modern/storage/core_adapter.py`): bridges
  core `whoosh.filedb.filestore.FileStorage` to the modern `SyncStorageProvider`
  interface, exported from `whoosh_modern.storage`.

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
- Configuration Engine: `SchemaEngine`, `AnalyzerEngine`, `DataSourceEngine`,
  `StorageEngine`, `SearchModelEngine`, `FacetEngine`, `PluginEngine`, `APIEngine`.
- Sprint F: Admin Studio (NiceGUI) + Synonym Manager remain.

[4.0.0.dev0]: https://github.com/dorel14/whoosh-NG/releases/tag/v4.0.0.dev0
