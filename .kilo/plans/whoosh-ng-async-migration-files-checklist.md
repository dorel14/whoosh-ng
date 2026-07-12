# Async Migration File List & Checklist

## Files to Migrate (Async‑first or async‑compatible)

| Component | Current Path | Action |
|-----------|--------------|--------|
| Core sync enforcement (audit) | `src/whoosh/**/*.py` | Ensure no `async`, `await`, `asyncio` usage |
| `run_sync` helper | `src/whoosh/utils/async.py` | New file – add implementation |
| PluginManager | `src/whoosh/plugins/manager.py` | Add async `register` support |
| Middleware base | `src/whoosh/middleware/base.py` | Add `AsyncMiddleware` class |
| Middleware context | `src/whoosh/middleware/context.py` | No change, just ensure type hints |
| Middleware chain | `src/whoosh/middleware/chain.py` | Detect and await async middleware |
| Event Bus | `src/whoosh/event_bus.py` | Convert to async‑only API (publish/subscribe are `async`) |
| Storage Provider sync base | `src/whoosh/vector/base.py` | Keep sync version |
| New async storage base | `src/whoosh/plugins/storage_base.py` | Add `AsyncStorageProvider` |
| New async vector base | `src/whoosh/plugins/vector_base.py` | Add `AsyncVectorProvider` |
| FastAPI plugin entry point | `src/whoosh_modern_fastapi/__init__.py` | New async plugin implementation |
| FastAPI plugin class | `src/whoosh_modern_fastapi/plugin.py` | Define `FastAPIPlugin` with async endpoints |
| Middleware metrics (example) | `src/whoosh/middleware/metrics.py` | Add async variant if needed |
| Tests – run_sync | `tests/test_run_sync.py` | New unit test |
| Tests – async PluginManager | `tests/test_plugin_manager_async.py` | New integration test |
| Tests – async middleware chain | `tests/test_middleware_async.py` | New test suite |
| Tests – FastAPI async endpoints | `tests/test_fastapi_async.py` | New integration test using `httpx.AsyncClient` |
| Benchmark suite | `tests/benchmark_async.py` | New benchmark file (pytest‑benchmark) |

## Developer Checklist (per large change)

1. **Create a dedicated branch** named `async/<feature>`.
2. **Add/modify files** as listed above.
3. **Run lint & type checks**:
   ```
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy src/whoosh --strict
   uv run pyright src/whoosh
   ```
4. **Run all tests** and ensure they pass:
   ```
   uv run pytest -q
   ```
5. **Run benchmarks** and verify async adds no regression to core performance:
   ```
   uv run pytest tests/benchmark_async.py --benchmark-save=async
   ```
6. **Update documentation** (`docs/user-guide/async-ecosystem.md`).
7. **Commit changes** with a clear message describing the large change (e.g., `feat(async): add run_sync helper`).
8. **Push branch** and open a PR.
9. **Ensure CI passes** (lint, type, tests, benchmarks).
10. **Merge** only after review; keep the commit history granular so each major change can be reverted independently.

### Commit Granularity Guideline
- **One commit per functional area** (e.g., run_sync helper, PluginManager async support, middleware async support, FastAPI plugin, tests, benchmarks).
- **Do not squash** unrelated changes.
- **Include** a reference to the corresponding issue/ticket.

---

*Generated for senior async lead developers.*
