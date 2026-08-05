"""Field index profiler for Whoosh-NG.

Decomposes field.index() into analyzer steps plus encoding overhead.

Measures:
- Time per token
- Objects created per token
- Per-step breakdown

Usage:
    from whoosh_modern.profiling import FieldIndexProfiler
    profiler = FieldIndexProfiler(field)
    items = list(profiler.profile_index(value))
    print(profiler.report())
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Iterator
from typing import Any


class _TimedStep:
    __slots__ = ("name", "_step", "_timings", "_counts")

    def __init__(
        self, name: str, step: Any, timings: dict[str, float], counts: dict[str, int]
    ) -> None:
        self.name = name
        self._step = step
        self._timings = timings
        self._counts = counts

    def __call__(self, tokens: Any, **kwargs: Any) -> list[Any]:
        t0 = time.perf_counter()
        result = list(self._step(tokens, **kwargs))
        elapsed = time.perf_counter() - t0
        self._timings[self.name] += elapsed
        self._counts[self.name] += len(result)
        return result


class FieldIndexProfiler:
    """Profile field.index() with detailed breakdown."""

    def __init__(self, field: Any) -> None:
        self._field = field
        self._patched: bool = False
        self._token_count: int = 0
        self._object_count: int = 0
        self._timings: dict[str, float] = defaultdict(float)
        self._counts: dict[str, int] = defaultdict(int)
        self._orig_analyzer = getattr(field, "analyzer", None)
        self._orig_format = getattr(field, "format", None)
        self._orig_items: list[Any] = []

    def profile_index(self, value: Any) -> list[tuple[bytes, int, float, bytes]]:
        """Profile field.index() and return items."""
        self._instrument_analyzer()
        t0 = time.perf_counter()
        items = list(self._field.index(value))
        total_time = time.perf_counter() - t0
        self._token_count += len(items)
        self._counts["total"] += len(items)
        self._timings["total"] += total_time
        self._uninstrument_analyzer()
        return items

    def _instrument_analyzer(self) -> None:
        """Instrument the analyzer to measure each step."""
        if self._patched:
            return
        self._patched = True
        analyzer = self._orig_analyzer
        if analyzer is None or not hasattr(analyzer, "items"):
            return

        self._orig_items = list(analyzer.items)
        analyzer.items = list(self._orig_items)

        for i, step in enumerate(analyzer.items):
            name = type(step).__name__
            analyzer.items[i] = _TimedStep(name, step, self._timings, self._counts)

    def _uninstrument_analyzer(self) -> None:
        """Restore original analyzer."""
        if not self._patched:
            return
        self._patched = False
        if self._orig_analyzer is not None and hasattr(self._orig_analyzer, "items"):
            self._orig_analyzer.items = list(self._orig_items)

    def report(self) -> str:
        """Generate a human-readable report."""
        if self._token_count == 0:
            return "No tokens indexed."

        lines = ["Field Index Profiling", "=" * 60, ""]
        lines.append(f"Total tokens: {self._token_count}")
        lines.append(f"Total objects created: {self._object_count}")
        total_time = self._timings.get("total", 0.0)
        lines.append(f"Total time: {total_time:.4f}s")
        if self._token_count > 0:
            lines.append(f"Time per token: {total_time / self._token_count * 1000:.4f} ms")
        lines.append("")

        lines.append("Per-step breakdown:")
        lines.append(
            f"{'Step':<25} {'Time (s)':>12} {'%':>8} {'Tokens':>10} {'Time/token (ms)':>18}"
        )
        lines.append("-" * 77)

        for name in sorted(self._timings.keys()):
            if name == "total":
                continue
            t = self._timings.get(name, 0.0)
            count = self._counts.get(name, 0)
            pct = t / total_time * 100 if total_time > 0 else 0.0
            tpt = t / count * 1000 if count > 0 else 0.0
            lines.append(f"  {name:<23} {t:>12.4f} {pct:>7.1f}% {count:>10} {tpt:>17.4f}")

        lines.append("-" * 77)
        lines.append(
            f"  {'Total':<23} {total_time:>12.4f} {'100.0':>8}% "
            f"{self._token_count:>10} {total_time / self._token_count * 1000:>17.4f}"
        )

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return results as a dict."""
        total_time = self._timings.get("total", 0.0)
        return {
            "token_count": self._token_count,
            "object_count": self._object_count,
            "total_time": total_time,
            "time_per_token_ms": total_time / self._token_count * 1000
            if self._token_count > 0
            else 0,
            "allocations_per_token": self._object_count / self._token_count
            if self._token_count > 0
            else 0,
            "steps": {
                name: {
                    "time": self._timings.get(name, 0.0),
                    "count": self._counts.get(name, 0),
                    "pct": self._timings.get(name, 0.0) / total_time * 100
                    if total_time > 0
                    else 0.0,
                    "time_per_token_ms": self._timings.get(name, 0.0)
                    / self._counts.get(name, 1)
                    * 1000,
                }
                for name in self._timings
                if name != "total"
            },
        }
