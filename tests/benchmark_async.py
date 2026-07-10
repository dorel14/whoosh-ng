from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh.utils.async_utils import run_sync


def _blocking_compute(x: int) -> int:
    return x * x


@pytest.mark.asyncio
async def test_run_sync_overhead(benchmark) -> None:
    result = await run_sync(_blocking_compute, 21)
    assert result == 441

    def _run() -> int:
        return asyncio.run(run_sync(_blocking_compute, 21))

    measured = benchmark(_run)
    assert measured == 441
