from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh.utils.async_utils import run_sync


def _blocking_compute(x: int) -> int:
    return x * x


def test_run_sync_overhead(benchmark) -> None:
    # Vérification de base (hors benchmark)
    result = asyncio.run(run_sync(_blocking_compute, 21))
    assert result == 441

    # Warmup: create the event loop and thread pool once so the benchmark
    # measures steady-state overhead instead of cold-start noise on CI.
    asyncio.run(run_sync(_blocking_compute, 21))

    def _run() -> int:
        return asyncio.run(run_sync(_blocking_compute, 21))

    measured = benchmark(_run)
    assert measured == 441
