"""PerDocWriter profiler for Whoosh-NG.

Instruments:
- add_field()
- start_doc()
- finish_doc()
- add_vector_items()

Usage:
    from whoosh_modern.profiling import PerDocWriterProfiler
    profiler = PerDocWriterProfiler(perdocwriter)
    # Use perdocwriter normally
    print(profiler.report())
"""

from __future__ import annotations

import time
from typing import Any


class PerDocWriterProfiler:
    """Profile PerDocWriter operations."""

    def __init__(self, perdocwriter: Any) -> None:
        self._perdocwriter = perdocwriter
        self._patched: bool = False
        self._add_field_count: int = 0
        self._start_doc_count: int = 0
        self._finish_doc_count: int = 0
        self._add_vector_items_count: int = 0
        self._add_field_time: float = 0.0
        self._start_doc_time: float = 0.0
        self._finish_doc_time: float = 0.0
        self._add_vector_items_time: float = 0.0
        self._orig_add_field = perdocwriter.add_field
        self._orig_start_doc = perdocwriter.start_doc
        self._orig_finish_doc = perdocwriter.finish_doc
        self._orig_add_vector_items = getattr(perdocwriter, "add_vector_items", None)

    def __enter__(self) -> PerDocWriterProfiler:
        self._patch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._unpatch()

    def _patch(self) -> None:
        if self._patched:
            return
        self._patched = True

        pdw = self._perdocwriter
        profiler = self

        orig_add_field = pdw.add_field
        orig_start_doc = pdw.start_doc
        orig_finish_doc = pdw.finish_doc
        orig_add_vector_items = self._orig_add_vector_items

        def timed_add_field(fieldname, field, value, length):
            t0 = time.perf_counter()
            result = orig_add_field(fieldname, field, value, length)
            elapsed = time.perf_counter() - t0
            profiler._add_field_time += elapsed
            profiler._add_field_count += 1
            return result

        def timed_start_doc(docnum):
            t0 = time.perf_counter()
            result = orig_start_doc(docnum)
            elapsed = time.perf_counter() - t0
            profiler._start_doc_time += elapsed
            profiler._start_doc_count += 1
            return result

        def timed_finish_doc():
            t0 = time.perf_counter()
            result = orig_finish_doc()
            elapsed = time.perf_counter() - t0
            profiler._finish_doc_time += elapsed
            profiler._finish_doc_count += 1
            return result

        def timed_add_vector_items(fieldname, field, items):
            t0 = time.perf_counter()
            result = orig_add_vector_items(fieldname, field, items)
            elapsed = time.perf_counter() - t0
            profiler._add_vector_items_time += elapsed
            profiler._add_vector_items_count += 1
            return result

        pdw.add_field = timed_add_field
        pdw.start_doc = timed_start_doc
        pdw.finish_doc = timed_finish_doc
        if orig_add_vector_items is not None:
            pdw.add_vector_items = timed_add_vector_items

    def _unpatch(self) -> None:
        if self._patched:
            pdw = self._perdocwriter
            pdw.add_field = self._orig_add_field
            pdw.start_doc = self._orig_start_doc
            pdw.finish_doc = self._orig_finish_doc
            if self._orig_add_vector_items is not None:
                pdw.add_vector_items = self._orig_add_vector_items
            self._patched = False

    def report(self) -> str:
        if not self._patched:
            return "PerDocWriterProfiler not active."

        lines = ["PerDocWriter Profiling", "=" * 60, ""]
        lines.append(f"add_field() calls      : {self._add_field_count}")
        lines.append(f"start_doc() calls      : {self._start_doc_count}")
        lines.append(f"finish_doc() calls     : {self._finish_doc_count}")
        lines.append(f"add_vector_items()     : {self._add_vector_items_count}")
        lines.append("")
        lines.append(f"{'Operation':<25} {'Calls':>8} {'Time (s)':>12} {'%':>8}")
        lines.append("-" * 57)

        total = (
            self._add_field_time
            + self._start_doc_time
            + self._finish_doc_time
            + self._add_vector_items_time
        )
        if total == 0:
            lines.append("  (no operations recorded)")
            return "\n".join(lines)

        ops = [
            ("add_field()", self._add_field_time, self._add_field_count),
            ("start_doc()", self._start_doc_time, self._start_doc_count),
            ("finish_doc()", self._finish_doc_time, self._finish_doc_count),
            ("add_vector_items()", self._add_vector_items_time, self._add_vector_items_count),
        ]
        for name, t, count in ops:
            pct = t / total * 100 if total > 0 else 0
            lines.append(f"  {name:<23} {count:>8} {t:>12.4f} {pct:>7.1f}%")

        lines.append("-" * 57)
        total_calls = (
            self._add_field_count
            + self._start_doc_count
            + self._finish_doc_count
            + self._add_vector_items_count
        )
        lines.append(f"  {'Total':<23} {total_calls:>8} {total:>12.4f} {'100.0':>8}%")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        total = (
            self._add_field_time
            + self._start_doc_time
            + self._finish_doc_time
            + self._add_vector_items_time
        )
        return {
            "add_field": {"count": self._add_field_count, "time": self._add_field_time},
            "start_doc": {"count": self._start_doc_count, "time": self._start_doc_time},
            "finish_doc": {"count": self._finish_doc_count, "time": self._finish_doc_time},
            "add_vector_items": {
                "count": self._add_vector_items_count,
                "time": self._add_vector_items_time,
            },
            "total_time": total,
            "add_field_pct": self._add_field_time / total * 100 if total > 0 else 0,
            "start_doc_pct": self._start_doc_time / total * 100 if total > 0 else 0,
            "finish_doc_pct": self._finish_doc_time / total * 100 if total > 0 else 0,
            "add_vector_items_pct": self._add_vector_items_time / total * 100 if total > 0 else 0,
        }
