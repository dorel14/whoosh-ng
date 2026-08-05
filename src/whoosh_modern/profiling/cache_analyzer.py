"""Cache analyzer and batch size optimizer for Whoosh-NG.

Provides tools to analyze field value repetition and determine
optimal batch sizes for indexing.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

# Type alias for field value counters
FieldCounter = Counter[str]


class CacheAnalyzer:
    """Analyzes field values to measure cache potential.

    Computes statistics about value repetition to determine
    if an LRU cache for analyzer results would be beneficial.
    """

    def __init__(self, fields: list[str] | None = None) -> None:
        self._fields = fields
        self._field_values: dict[str, list[str]] = {}
        self._field_value_counts: dict[str, FieldCounter] = {}
        self._total_values: int = 0

    def record_document(self, doc: dict[str, Any]) -> None:
        """Record a document's field values for analysis."""
        fields = self._fields or list(doc.keys())
        for field in fields:
            value = doc.get(field, "")
            if field not in self._field_values:
                self._field_values[field] = []
                self._field_value_counts[field] = Counter()
            str_value = str(value) if value is not None else ""
            self._field_values[field].append(str_value)
            self._field_value_counts[field][str_value] += 1
            self._total_values += 1

    def record_value(self, field: str, value: Any) -> None:
        """Record a single field value."""
        if field not in self._field_values:
            self._field_values[field] = []
            self._field_value_counts[field] = Counter()
        str_value = str(value) if value is not None else ""
        self._field_values[field].append(str_value)
        self._field_value_counts[field][str_value] += 1
        self._total_values += 1

    @property
    def fields(self) -> list[str]:
        return list(self._field_values.keys())

    def unique_count(self, field: str) -> int:
        return len(self._field_value_counts.get(field, Counter()))

    def total_count(self, field: str) -> int:
        return len(self._field_values.get(field, []))

    def repetition_ratio(self, field: str) -> float:
        unique = self.unique_count(field)
        if unique == 0:
            return 0.0
        return self.total_count(field) / unique

    def cache_savings(self, field: str, cache_size: int = 10000) -> float:
        counter = self._field_value_counts.get(field, Counter())
        if not counter:
            return 0.0
        total = sum(counter.values())
        if total == 0:
            return 0.0
        cached_count = sum(count for _, count in counter.most_common(cache_size))
        return (cached_count / total) * 100

    @property
    def total_unique_values(self) -> int:
        return sum(len(counter) for counter in self._field_value_counts.values())

    @property
    def total_values(self) -> int:
        return self._total_values

    def report(self) -> str:
        lines: list[str] = []
        lines.append("Cache Analysis")
        lines.append("=" * 60)
        for field in sorted(self._field_values.keys()):
            total = self.total_count(field)
            unique = self.unique_count(field)
            ratio = self.repetition_ratio(field)
            savings = self.cache_savings(field)
            bar = "#" * int(savings / 5)
            lines.append(f"  {field:<20}")
            lines.append(f"    total: {total}, unique: {unique}, ratio: {ratio:.1f}x")
            lines.append(f"    cache savings (10k): {savings:.1f}% {bar}")
        lines.append("-" * 60)
        lines.append(f"  Total values: {self.total_values}")
        lines.append(f"  Total unique: {self.total_unique_values}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_values": self.total_values,
            "total_unique_values": self.total_unique_values,
            "fields": {
                field: {
                    "total": self.total_count(field),
                    "unique": self.unique_count(field),
                    "repetition_ratio": round(self.repetition_ratio(field), 2),
                    "cache_savings_10k": round(self.cache_savings(field), 1),
                }
                for field in self.fields
            },
        }


class BatchSizeOptimizer:
    """Analyzes optimal batch size for indexing."""

    def __init__(self, writer: Any, source: Any) -> None:
        self._writer = writer
        self._source = source
        self._results: list[dict[str, Any]] = []

    def benchmark(
        self,
        batch_sizes: list[int] | None = None,
        docs_per_size: int = 5000,
    ) -> list[dict[str, Any]]:
        if batch_sizes is None:
            batch_sizes = [100, 500, 1000, 2500, 5000, 10000]

        results = []
        for batch_size in batch_sizes:
            result = self._run_benchmark(batch_size, docs_per_size)
            results.append(result)
            self._results.append(result)

        return results

    def _run_benchmark(self, batch_size: int, docs_count: int) -> dict[str, Any]:
        import time

        start = time.perf_counter()
        count = 0
        for batch in self._source.stream_batches(batch_size=batch_size):
            self._writer.add_batch(batch)
            count += len(batch)
            if count >= docs_count:
                break
        elapsed = time.perf_counter() - start
        docs_per_sec = count / elapsed if elapsed > 0 else 0.0
        return {
            "batch_size": batch_size,
            "docs_indexed": count,
            "elapsed_s": round(elapsed, 3),
            "docs_per_sec": round(docs_per_sec, 1),
        }

    def report(self) -> str:
        lines: list[str] = []
        lines.append("Batch Size Optimization")
        lines.append("=" * 60)
        lines.append(f"  {'Batch Size':<12} {'Docs':<8} {'Time':<10} {'Docs/s':<10}")
        lines.append("  " + "-" * 40)
        for result in self._results:
            lines.append(
                f"  {result['batch_size']:<12} "
                f"{result['docs_indexed']:<8} "
                f"{result['elapsed_s']:<10.3f} "
                f"{result['docs_per_sec']:<10.1f}"
            )
        if self._results:
            best = max(self._results, key=lambda x: x["docs_per_sec"])
            lines.append("-" * 60)
            lines.append(
                f"  Optimal batch size: {best['batch_size']} ({best['docs_per_sec']:.1f} docs/s)"
            )
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "results": self._results,
            "optimal_batch_size": (
                max(self._results, key=lambda x: x["docs_per_sec"])["batch_size"]
                if self._results
                else None
            ),
        }
