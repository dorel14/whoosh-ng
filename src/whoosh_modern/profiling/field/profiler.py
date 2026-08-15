"""Field profiler for Whoosh-NG.

Provides per-field cost analysis to identify which fields
are the most expensive to index.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any


class FieldProfiler:
    """Profiler for per-field indexing costs.

    Tracks time spent indexing each field to identify
    the most expensive fields.

    Example::

        profiler = FieldProfiler()
        for field_name, value in doc.items():
            with profiler.step(field_name):
                writer._add_field(field_name, value)
        print(profiler.report())
    """

    def __init__(self) -> None:
        self._field_times: dict[str, float] = defaultdict(float)
        self._field_counts: dict[str, int] = defaultdict(int)
        self._field_token_counts: dict[str, int] = defaultdict(int)
        self._active_field: str | None = None
        self._active_start: float | None = None

    def step(self, field_name: str) -> _FieldStepContext:
        """Start profiling a field."""
        return _FieldStepContext(self, field_name)

    def _start_field(self, field_name: str) -> None:
        """Start timing a field."""
        if self._active_field is not None and self._active_start is not None:
            self._stop_field()
        self._active_field = field_name
        self._active_start = time.perf_counter()

    def _stop_field(self) -> None:
        """Stop timing the active field."""
        if self._active_field is not None and self._active_start is not None:
            elapsed = time.perf_counter() - self._active_start
            self._field_times[self._active_field] += elapsed
            self._field_counts[self._active_field] += 1
            self._active_field = None
            self._active_start = None

    def record_tokens(self, field_name: str, count: int) -> None:
        """Record token count for a field."""
        self._field_token_counts[field_name] += count

    @property
    def field_times(self) -> dict[str, float]:
        """Return total time per field."""
        return dict(self._field_times)

    @property
    def field_counts(self) -> dict[str, int]:
        """Return document count per field."""
        return dict(self._field_counts)

    @property
    def total_time(self) -> float:
        return sum(self._field_times.values())

    @property
    def total_documents(self) -> int:
        return sum(self._field_counts.values())

    def report(self) -> str:
        """Return a human-readable profiling report."""
        lines: list[str] = []
        lines.append("Field Profiling")
        lines.append("=" * 60)

        total_time = self.total_time
        sorted_fields = sorted(self._field_times.items(), key=lambda x: x[1], reverse=True)

        for field_name, elapsed in sorted_fields:
            count = self._field_counts.get(field_name, 0)
            tokens = self._field_token_counts.get(field_name, 0)
            pct = (elapsed / total_time * 100) if total_time > 0 else 0.0
            bar = "#" * int(pct / 2)
            avg_us = (elapsed / count * 1_000_000) if count > 0 else 0.0
            lines.append(f"  {field_name:<20} ... {elapsed:>8.3f}s  ({pct:5.1f}%) {bar}")
            lines.append(f"    docs={count}, tokens={tokens}, avg={avg_us:.1f}us/doc")

        lines.append("-" * 60)
        lines.append(f"  Total fields: {len(self._field_times)}")
        lines.append(f"  Total time: {total_time:.3f}s")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return profiling data as a dictionary."""
        sorted_fields = sorted(self._field_times.items(), key=lambda x: x[1], reverse=True)
        return {
            "total_time": round(self.total_time, 3),
            "total_documents": self.total_documents,
            "fields": [
                {
                    "name": name,
                    "elapsed": round(elapsed, 3),
                    "documents": self._field_counts.get(name, 0),
                    "tokens": self._field_token_counts.get(name, 0),
                    "avg_us_per_doc": round(
                        (elapsed / self._field_counts.get(name, 1)) * 1_000_000, 1
                    ),
                }
                for name, elapsed in sorted_fields
            ],
        }


class _FieldStepContext:
    """Context manager for profiling a single field."""

    def __init__(self, profiler: FieldProfiler, field_name: str) -> None:
        self._profiler = profiler
        self._field_name = field_name

    def __enter__(self) -> _FieldStepContext:
        self._profiler._start_field(self._field_name)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self._profiler._stop_field()
