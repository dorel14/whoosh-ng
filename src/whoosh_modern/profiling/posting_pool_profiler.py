"""PostingPool profiler for Whoosh-NG.

Instruments:
- PostingPool.add()
- PostingPool.save()

Usage:
    from whoosh_modern.profiling import PostingPoolProfiler
    profiler = PostingPoolProfiler(pool)
    # Use pool normally; profiler collects timing
    print(profiler.report())
"""

from __future__ import annotations

import time
from typing import Any


class PostingPoolProfiler:
    """Profile PostingPool operations."""

    def __init__(self, pool: Any) -> None:
        self._pool = pool
        self._patched: bool = False
        self._add_count: int = 0
        self._save_count: int = 0
        self._add_time: float = 0.0
        self._save_time: float = 0.0
        self._bytes_added: int = 0
        self._orig_add = pool.add
        self._orig_save = pool.save

    def __enter__(self) -> PostingPoolProfiler:
        self._patch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._unpatch()

    def _patch(self) -> None:
        if self._patched:
            return
        self._patched = True

        pool = self._pool
        profiler = self

        orig_add = pool.add
        orig_save = pool.save

        def timed_add(item):
            t0 = time.perf_counter()
            result = orig_add(item)
            elapsed = time.perf_counter() - t0
            profiler._add_time += elapsed
            profiler._add_count += 1
            return result

        def timed_save():
            t0 = time.perf_counter()
            result = orig_save()
            elapsed = time.perf_counter() - t0
            profiler._save_time += elapsed
            profiler._save_count += 1
            return result

        pool.add = timed_add
        pool.save = timed_save

    def _unpatch(self) -> None:
        if self._patched:
            pool = self._pool
            pool.add = self._orig_add
            pool.save = self._orig_save
            self._patched = False

    def report(self) -> str:
        if not self._patched:
            return "PostingPoolProfiler not active."

        lines = ["PostingPool Profiling", "=" * 60, ""]
        lines.append(f"add() calls   : {self._add_count}")
        lines.append(f"save() calls  : {self._save_count}")
        lines.append("")
        lines.append(f"{'Operation':<20} {'Calls':>8} {'Time (s)':>12} {'%':>8}")
        lines.append("-" * 52)

        total = self._add_time + self._save_time
        if total == 0:
            lines.append("  (no operations recorded)")
            return "\n".join(lines)

        ops = [
            ("add()", self._add_time, self._add_count),
            ("save()", self._save_time, self._save_count),
        ]
        for name, t, count in ops:
            pct = t / total * 100 if total > 0 else 0
            lines.append(f"  {name:<18} {count:>8} {t:>12.4f} {pct:>7.1f}%")

        lines.append("-" * 52)
        lines.append(
            f"  {'Total':<18} {self._add_count + self._save_count:>8} {total:>12.4f} {'100.0':>8}%"
        )
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        total = self._add_time + self._save_time
        return {
            "add": {"count": self._add_count, "time": self._add_time},
            "save": {"count": self._save_count, "time": self._save_time},
            "total_time": total,
            "add_pct": self._add_time / total * 100 if total > 0 else 0,
            "save_pct": self._save_time / total * 100 if total > 0 else 0,
        }
