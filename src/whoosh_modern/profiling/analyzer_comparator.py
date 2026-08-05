"""Analyzer comparator with standardized benchmarks.

Compares analyzers on common datasets and metrics:
- StandardAnalyzer
- StemmingAnalyzer
- LanguageAnalyzer

Usage:
    from whoosh_modern.profiling import AnalyzerComparator
    comparator = AnalyzerComparator()
    results = comparator.compare_all(docs, sizes=[10000, 50000, 100000])
    print(comparator.report())
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from whoosh.analysis import LanguageAnalyzer, StandardAnalyzer, StemmingAnalyzer
from whoosh_modern.profiling.analyzer_profiler import AnalyzerStepProfiler


class AnalyzerResult:
    """Results for a single analyzer on a single dataset size."""

    def __init__(self, name: str, size: int) -> None:
        self.name = name
        self.size = size
        self.total_time: float = 0.0
        self.token_count: int = 0
        self.text_count: int = 0
        self.steps: dict[str, dict[str, Any]] = {}

    @property
    def throughput(self) -> float:
        return self.text_count / self.total_time if self.total_time > 0 else 0.0

    @property
    def avg_tokens_per_text(self) -> float:
        return self.token_count / self.text_count if self.text_count > 0 else 0.0


class AnalyzerComparator:
    """Compare multiple analyzers on standardized benchmarks."""

    def __init__(self) -> None:
        self._results: list[AnalyzerResult] = []
        self._analyzers = {
            "StandardAnalyzer": StandardAnalyzer(),
            "StemmingAnalyzer": StemmingAnalyzer(),
            "LanguageAnalyzer": LanguageAnalyzer(lang="en"),
        }

    def compare_all(
        self, docs: list[dict[str, Any]], sizes: list[int] | None = None
    ) -> dict[str, list[AnalyzerResult]]:
        """Compare all analyzers on the given documents.

        :param docs: list of document dicts
        :param sizes: list of dataset sizes to test (default: [10000, 50000, 100000])
        :returns: dict mapping analyzer name to list of results
        """
        if sizes is None:
            sizes = [10000, 50000, 100000]

        results: dict[str, list[AnalyzerResult]] = {name: [] for name in self._analyzers}

        for size in sizes:
            texts = self._extract_texts(docs, size)
            for name, analyzer in self._analyzers.items():
                result = self._benchmark_analyzer(name, analyzer, texts)
                results[name].append(result)
                self._results.append(result)

        return results

    def _extract_texts(self, docs: list[dict[str, Any]], max_size: int) -> list[str]:
        """Extract text values from documents up to max_size."""
        texts: list[str] = []
        for doc in docs:
            if len(texts) >= max_size:
                break
            for v in doc.values():
                if isinstance(v, str) and len(v) < 500:
                    texts.append(v)
                    if len(texts) >= max_size:
                        break
        return texts

    def _benchmark_analyzer(self, name: str, analyzer: Any, texts: list[str]) -> AnalyzerResult:
        """Benchmark a single analyzer on a list of texts."""
        result = AnalyzerResult(name, len(texts))
        profiler = AnalyzerStepProfiler(analyzer)

        t0 = time.perf_counter()
        for text in texts:
            tokens = profiler.profile_text(text)
        total_time = time.perf_counter() - t0

        result.total_time = total_time
        result.token_count = profiler._token_count
        result.text_count = profiler._text_count
        result.steps = profiler.to_dict().get("steps", {})

        profiler._reset()
        return result

    def report(self) -> str:
        lines = ["Analyzer Comparison Report", "=" * 60, ""]
        lines.append(f"Analyzers: {', '.join(self._analyzers.keys())}")
        lines.append(f"Total benchmarks: {len(self._results)}")
        lines.append("")

        # Group by size
        by_size: dict[int, list[AnalyzerResult]] = defaultdict(list)
        for result in self._results:
            by_size[result.size].append(result)

        for size in sorted(by_size.keys()):
            lines.append(f"=== Dataset size: {size} texts ===")
            lines.append("")
            lines.append(
                f"{'Analyzer':<20} {'Time (s)':<12} {'Tokens':<12} "
                f"{'Throughput':<15} {'Avg tokens/text':<18}"
            )
            lines.append("-" * 77)

            results = by_size[size]
            for result in sorted(results, key=lambda r: r.total_time):
                lines.append(
                    f"{result.name:<20} {result.total_time:<12.3f} "
                    f"{result.token_count:<12} {result.throughput:<15.1f} "
                    f"{result.avg_tokens_per_text:<18.1f}"
                )

            lines.append("")

            # Per-step breakdown for each analyzer
            for result in sorted(results, key=lambda r: r.total_time):
                lines.append(f"  {result.name} - Per-step breakdown:")
                step_lines = []
                for step_name, step_data in result.steps.items():
                    step_time = step_data.get("time", 0.0)
                    step_tokens = step_data.get("tokens", 0)
                    pct = (step_time / result.total_time * 100) if result.total_time > 0 else 0.0
                    step_lines.append(
                        f"    {step_name:<20} {step_time:<12.4f}s {step_tokens:<12} {pct:<8.1f}%"
                    )
                lines.extend(step_lines)
                lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            name: [
                {
                    "size": r.size,
                    "time": r.total_time,
                    "tokens": r.token_count,
                    "throughput": r.throughput,
                    "avg_tokens_per_text": r.avg_tokens_per_text,
                    "steps": r.steps,
                }
                for r in results
            ]
            for name, results in self._results_by_analyzer().items()
        }

    def _results_by_analyzer(self) -> dict[str, list[AnalyzerResult]]:
        by_name: dict[str, list[AnalyzerResult]] = defaultdict(list)
        for result in self._results:
            by_name[result.name].append(result)
        return dict(by_name)
