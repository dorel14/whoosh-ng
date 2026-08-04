"""Analyzer profiling for Whoosh-NG.

Measures the cost of:
- tokenizer
- stemming
- token filters
on representative text samples.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from typing import Any, Callable, Iterator


class AnalyzerProfiler:
    """Profiler for analyzer components.

    Example::

        profiler = AnalyzerProfiler()
        for text in texts:
            profiler.profile(text, analyzer)
        print(profiler.report())
    """

    def __init__(self) -> None:
        self._steps: OrderedDict[str, AnalyzerStepTimer] = OrderedDict()
        self._texts: int = 0

    def profile(self, text: str, analyzer: Callable[[str], Iterator[Any]]) -> None:
        """Profile one text through the analyzer."""
        self._texts += 1
        tokens = list(analyzer(text))
        self._steps.setdefault("tokenizer", AnalyzerStepTimer("tokenizer"))
        self._steps["tokenizer"].record_tokens(len(tokens))

    @property
    def total_time(self) -> float:
        return sum(s.elapsed for s in self._steps.values())

    @property
    def total_tokens(self) -> int:
        return sum(s.tokens for s in self._steps.values())

    def report(self) -> str:
        lines = ["Analyzer Profiling", "=" * 50, ""]
        for step in self._steps.values():
            pct = (step.elapsed / self.total_time * 100) if self.total_time > 0 else 0.0
            lines.append(
                f"  {step.name:<20} ... {step.elapsed:>8.3f}s  "
                f"({pct:5.1f}%) tokens={step.tokens}"
            )
        lines.append("-" * 50)
        lines.append(f"  texts={self._texts} tokens={self.total_tokens}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "texts": self._texts,
            "total_tokens": self.total_tokens,
            "steps": {
                name: {
                    "elapsed": round(s.elapsed, 3),
                    "tokens": s.tokens,
                }
                for name, s in self._steps.items()
            },
        }


class AnalyzerStepTimer:
    """Measures elapsed time for a single analyzer substep."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._start: float | None = None
        self._elapsed: float = 0.0
        self._count: int = 0
        self._tokens: int = 0

    def start(self) -> None:
        if self._start is None:
            self._start = time.perf_counter()

    def stop(self) -> float:
        if self._start is not None:
            delta = time.perf_counter() - self._start
            self._elapsed += delta
            self._count += 1
            self._start = None
            return delta
        return 0.0

    def record_tokens(self, count: int) -> None:
        self._tokens += count

    @property
    def elapsed(self) -> float:
        return self._elapsed

    @property
    def count(self) -> int:
        return self._count

    @property
    def tokens(self) -> int:
        return self._tokens
