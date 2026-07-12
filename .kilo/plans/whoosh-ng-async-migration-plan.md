# Whoosh‑NG Async Ecosystem Migration Plan

## 1. Core Sync Enforcement
- Audit all `src/whoosh/**/*.py` for `async`, `await`, `asyncio`.
- Reject any usage of `asyncio.run`, `async def`, or `await` inside core modules.
- Add a pre‑commit hook that errors if violations are detected.

## 2. `run_sync` Bridge
```python
# src/whoosh/utils/async.py
import asyncio
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")

async def run_sync(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Execute a synchronous function in a thread pool.

    All async plugin code that needs to call sync core methods should use this helper.
    """
    return await asyncio.to_thread(func, *args, **kwargs)
```
- Add comprehensive docstrings and type hints.
- Run `ruff` and `mypy` checks to ensure no type errors.

## 3. PluginManager Async Support
- Extend `PluginManager.register()` to accept both sync and async `Plugin` classes.
- Detect `async def register(self, registry):` and invoke it inside an event loop using `run_sync` if called from sync context.
- Preserve existing conflict detection and dependency resolution logic.

## 4. Async Base Classes
- **Storage**
```python
# src/whoosh/plugins/storage_base.py
class AsyncStorageProvider:
    async def write(self, key: str, data: bytes) -> None: ...
```
- **Vector**
```python
class AsyncVectorProvider:
    async def asearch(self, vector: list[float]) -> list[Hit]: ...
```
- Keep sync counterparts in `storage_base.SyncStorageProvider`.

## 5. FastAPI Async Plugin
- Create `src/whoosh_modern_fastapi/__init__.py` with FastAPI app factory.
- Endpoints defined with `async def`.
- All core calls wrapped with `await run_sync(...)`.
- Expose plugin via entry point `whoosh.plugins=whoosh_modern_fastapi.plugin:FastAPIPlugin`.

## 6. Middleware Engine
- Middleware classes can now inherit from either `Middleware` (sync) or `AsyncMiddleware`.
- `MiddlewareChain` executes sync middleware immediately and awaits async middleware.
- Support mixed ordering: sync first → async → sync.
- Add tests validating execution order and exception propagation.

## 7. Documentation
- Add `docs/user-guide/async-ecosystem.md` explaining:
  * Boundaries between sync core and async ecosystem.
  * Usage of `run_sync`.
  * Recommended patterns for plugin authors.
- Update README with async ecosystem section.

## 8. Code Quality
- Run `ruff check .` and `ruff format .`.
- Run `mypy src/whoosh` with `--strict`.
- Ensure `pyright` passes without errors.

## 9. Tests
- **Unit tests** for `run_sync`, middleware execution order, and PluginManager async registration.
- **Integration tests** for FastAPI async endpoints using `httpx.AsyncClient`.
- **Benchmark tests** comparing:
  * Sync search `Searcher.search` via `index.search`.
  * Async search `Searcher.asearch` via `run_sync` wrapper.
- All tests must pass under `pytest -q`.

## 10. Benchmarking Strategy
- Use `pytest-benchmark` to measure execution times.
- Suite includes:
  * Indexing 10k documents – sync vs async wrapper.
  * Searching top‑10 results – sync vs async wrapper.
- Document results in `docs/benchmarks/async.md`.

## 11. Deployment Checklist
- Ensure `venv` located at repo root (`.venv`).
- `pip install .[dev]` installs core and dev dependencies.
- `uv run test.yml` runs CI pipeline.
- No lint, type, or mypy errors.

> **Senior Lead Note**: All changes must be peer‑reviewed, no code is merged until the provided tests, lints, and benchmarks validate the async architecture. No dev should set up an async runtime inside the core.

---

**Author**: Kilo
**Date**: 2026-06-21
