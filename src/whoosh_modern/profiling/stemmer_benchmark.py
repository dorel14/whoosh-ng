"""Isolated stemmer benchmark.

Compares stemmers on the same corpus:
- StemFilter (whoosh default / porter-like)
- PyStemmerFilter (if py-stemmer is available)

Usage:
    from whoosh_modern.profiling import StemmerBenchmark
    bench = StemmerBenchmark()
    bench.run(texts)
    print(bench.report())
"""

from __future__ import annotations

import time
from contextlib import suppress
from typing import Any

from whoosh.analysis import StemFilter
from whoosh.analysis.morph import PyStemmerFilter


class _Token:
    __slots__ = ("text", "stopped", "pos")

    def __init__(self, text: str, stopped: bool = False, pos: int = 0) -> None:
        self.text = text
        self.stopped = stopped
        self.pos = pos


class StemmerBenchmark:
    """Isolated stemmer benchmark."""

    def __init__(self) -> None:
        self._stemmers: dict[str, Any] = {
            "StemFilter": StemFilter(),
        }
        with suppress(ImportError):
            self._stemmers["PyStemmer"] = PyStemmerFilter("english")
        self._results: dict[str, dict[str, Any]] = {}

    def run(self, texts: list[str], warmup: bool = True) -> None:
        """Run benchmark on given texts.

        :param texts: list of texts to stem
        :param warmup: if True, run a warmup pass to avoid cold-start bias
        """
        for name, stemmer in self._stemmers.items():
            if warmup:
                self._warmup(stemmer, texts)
            tokens = 0
            t0 = time.perf_counter()
            for text in texts:
                words = text.split()
                tokens += len(words)
                list(stemmer(iter(_Token(w) for w in words)))
            total_time = time.perf_counter() - t0
            self._results[name] = {
                "total_time": total_time,
                "token_count": tokens,
                "tokens_per_second": tokens / total_time if total_time > 0 else 0,
            }

    def _warmup(self, stemmer: Any, texts: list[str]) -> None:
        """Warmup the stemmer with a small sample."""
        sample = texts[: min(100, len(texts))]
        for text in sample:
            words = text.split()
            list(stemmer(iter(_Token(w) for w in words)))

    def report(self) -> str:
        """Generate a human-readable report."""
        if not self._results:
            return "No results. Call run() first."

        lines = ["Stemmer Benchmark", "=" * 50, ""]
        lines.append(f"{'Stemmer':<15} {'Tokens/s':<15} {'Time (s)':<12} {'Tokens':<12}")
        lines.append("-" * 54)

        for name, result in sorted(self._results.items()):
            lines.append(
                f"{name:<15} "
                f"{result['tokens_per_second']:<15.0f} "
                f"{result['total_time']:<12.4f} "
                f"{result['token_count']:<12}"
            )

        return "\n".join(lines)

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Return results as a dict."""
        return self._results
