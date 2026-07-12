# Changelog

All notable changes to Whoosh-NG are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0.dev0] - Unreleased

### Added
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

### Changed
- Renamed distribution from `whoosh-reloaded` to **`whoosh-ng`**. The import
  namespace remains `whoosh` for backward compatibility.
- Documentation site moved to GitHub Pages: https://dorel14.github.io/Whoosh-NG/
- Required Python version is now `>=3.11`.
- Packaging cleaned: removed redundant `requirements*.txt`; consolidated extras
  in `pyproject.toml`.
- Type annotations modernized: `mypy src/whoosh` reports 0 errors. `py.typed`
  marker shipped.

### In Progress (tracked in `.kilo/plans/1783617590838-whoosh-ng-consolidated-plan.md`)
- Async ecosystem: `run_sync` bridge, async plugin registration,
  `AsyncStorageProvider`/`AsyncVectorProvider` bases, fully async FastAPI plugin.
- Relocation of `CompressionMiddleware`/`EncryptionMiddleware` to the backend/store
  layer (per architecture decision).
- `pyright` added to CI and progressive strict typing.
- Jekyll documentation (EN/FR) finalization and publication.

[4.0.0.dev0]: https://github.com/dorel14/whoosh-NG/releases/tag/v4.0.0.dev0
