"""Analyzer step-by-step profiler.

Measures time and token counts per pipeline step:
- Tokenizer
- LowercaseFilter
- StopFilter
- StemFilter
- CharsetFilter
- Custom Filters

Usage:
    from whoosh_modern.profiling import AnalyzerStepProfiler
    profiler = AnalyzerStepProfiler(analyzer)
    for doc in docs:
        tokens = profiler.profile_text(text)
    print(profiler.report())
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any


class _TimedStep:
    """Wrapper around a pipeline step that measures execution time and token counts."""

    __slots__ = ("name", "_step", "_timings", "_counts")

    def __init__(
        self, name: str, step: Any, timings: dict[str, list[float]], counts: dict[str, int]
    ) -> None:
        self.name = name
        self._step = step
        self._timings = timings
        self._counts = counts

    def __call__(self, tokens: Any) -> Any:
        t0 = time.perf_counter()
        result = list(self._step(tokens))
        elapsed = time.perf_counter() - t0
        self._timings[self.name].append(elapsed)
        self._counts[self.name] += len(result)
        return iter(result)


class AnalyzerStepProfiler:
    """Profile each step of an analyzer pipeline."""

    def __init__(self, analyzer: Any) -> None:
        self._analyzer = analyzer
        self._step_timings: dict[str, list[float]] = defaultdict(list)
        self._step_counts: dict[str, int] = defaultdict(int)
        self._text_count: int = 0
        self._token_count: int = 0
        self._instrumented: bool = False
        self._timed_steps: list[_TimedStep] = []

    def _instrument(self) -> None:
        if self._instrumented:
            return
        self._instrumented = True
        self._timed_steps = []
        items = getattr(self._analyzer, "items", None)
        if items is None:
            return
        if getattr(self, "_original_items", None) is None:
            self._original_items = list(items)
        items[:] = self._original_items
        for i, step in enumerate(items):
            name = type(step).__name__
            timed = _TimedStep(name, step, self._step_timings, self._step_counts)
            self._timed_steps.append(timed)
            items[i] = timed

    def _reset(self) -> None:
        if getattr(self, "_original_items", None) is not None:
            items = getattr(self._analyzer, "items", None)
            if items is not None:
                items[:] = self._original_items
        self._instrumented = False
        self._timed_steps = []
        self._step_timings.clear()
        self._step_counts.clear()
        self._text_count = 0
        self._token_count = 0

    def profile_text(self, text: str) -> list[Any]:
        """Profile analysis of a single text and return tokens."""
        self._instrument()
        self._text_count += 1
        t0 = time.perf_counter()
        tokens = list(self._analyzer(text))
        total = time.perf_counter() - t0
        self._step_timings["__total__"].append(total)
        self._step_counts["__total__"] += len(tokens)
        self._token_count += len(tokens)
        return tokens

    def report(self) -> str:
        lines = ["Analyzer Step Profiling", "=" * 50, ""]
        lines.append(f"Texts analyzed: {self._text_count}")
        lines.append(f"Total tokens: {self._token_count}")
        lines.append("")

        total_times = self._step_timings.get("__total__", [])
        if total_times:
            total_time = sum(total_times)
            avg = total_time / len(total_times) if total_times else 0.0
            lines.append(f"Total analysis time: {total_time:.3f}s")
            lines.append(f"Avg per text: {avg * 1000:.2f}ms")
            lines.append(f"Throughput: {len(total_times) / total_time:.0f} texts/s")
            lines.append("")

        lines.append("Per-step breakdown:")
        lines.append(f"{'Etape':<20} {'Temps (s)':<12} {'Tokens':<12} {'%':<8}")
        lines.append("-" * 54)

        total_time = sum(total_times)
        seen = set()
        for timed in self._timed_steps:
            name = timed.name
            if name in seen:
                continue
            seen.add(name)
            times = self._step_timings.get(name, [])
            tokens = self._step_counts.get(name, 0)
            step_total = sum(times)
            pct = (step_total / total_time * 100) if total_time > 0 else 0.0
            lines.append(f"{name:<20} {step_total:<12.4f} {tokens:<12} {pct:<8.1f}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        total_time = sum(self._step_timings.get("__total__", []))
        return {
            "text_count": self._text_count,
            "token_count": self._token_count,
            "total_time": total_time,
            "steps": {
                name: {
                    "time": sum(times),
                    "tokens": self._step_counts.get(name, 0),
                }
                for name, times in self._step_timings.items()
                if name != "__total__"
            },
        }
