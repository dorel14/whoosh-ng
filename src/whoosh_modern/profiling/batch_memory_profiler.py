"""Batch memory profiler for Whoosh-NG.

Measures memory usage during batch indexing to understand why some batch
sizes outperform others.

Usage::

    profiler = BatchMemoryProfiler()
    with profiler.measure():
        writer.add_batch(batch)
    profiler.set_batch_metrics(terms=..., postings=..., blocks=...)
    print(profiler.report())
"""

from __future__ import annotations

import gc
import tracemalloc
from typing import Any


class BatchMemoryProfiler:
    """Measures memory usage for a single batch indexing operation."""

    _BATCH_REFERENCES: dict[int, dict[str, int]] = {
        250: {"terms": 12_000, "postings": 44_000, "blocks": 11_000},
        1000: {"terms": 55_000, "postings": 220_000, "blocks": 72_000},
    }

    def __init__(self) -> None:
        self._snapshots: list[Any] = []
        self._gc_counts: list[tuple[int, int, int]] = []
        self._peak_mb: float = 0.0
        self._start_objects: int = 0
        self._end_objects: int = 0
        self._terms: int = 0
        self._postings: int = 0
        self._blocks: int = 0
        self._batch_size: int | None = None

    def measure(self):
        return self

    def __enter__(self) -> BatchMemoryProfiler:
        gc.collect()
        self._gc_counts.append(gc.get_count())
        tracemalloc.start()
        self._snapshots.append(tracemalloc.take_snapshot())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if tracemalloc.is_tracing():
            current = tracemalloc.take_snapshot()
            self._snapshots.append(current)
            _, peak = tracemalloc.get_traced_memory()
            self._peak_mb = peak / (1024 * 1024)
            tracemalloc.stop()
        gc.collect()
        self._gc_counts.append(gc.get_count())

    def set_batch_metrics(
        self, *, batch_size: int | None = None, terms: int = 0, postings: int = 0, blocks: int = 0
    ) -> None:
        self._batch_size = batch_size
        self._terms = terms
        self._postings = postings
        self._blocks = blocks

    def report(self) -> str:
        if len(self._snapshots) < 2:
            return "BatchMemoryProfiler: not enough data"
        before = self._snapshots[0]
        after = self._snapshots[-1]
        stats = after.compare_to(before, "lineno")
        top = stats[:10]
        lines = ["Batch Memory Profiling", "=" * 40, ""]
        lines.append(f"Batch size      : {self._batch_size}")
        lines.append(f"Memory peak     : {self._peak_mb:.2f} MB")
        lines.append(f"Unique terms    : {self._terms:,}")
        lines.append(f"Postings count  : {self._postings:,}")
        lines.append(f"Blocks          : {self._blocks:,}")
        if self._batch_size in self._BATCH_REFERENCES:
            ref = self._BATCH_REFERENCES[self._batch_size]
            lines.append("")
            lines.append("Reference values:")
            lines.append(f"  terms       : {ref['terms']:,}")
            lines.append(f"  postings    : {ref['postings']:,}")
            lines.append(f"  blocks      : {ref['blocks']:,}")
        lines.append("")
        for stat in top:
            lines.append(f"  {stat}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshots": len(self._snapshots),
            "peak_mb": round(self._peak_mb, 2),
            "terms": self._terms,
            "postings": self._postings,
            "blocks": self._blocks,
            "batch_size": self._batch_size,
        }
