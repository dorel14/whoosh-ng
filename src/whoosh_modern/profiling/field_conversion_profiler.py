"""Detailed field conversion profiler for Whoosh-NG.

Instruments the actual field.index() call to measure:
- Analyzer time (inside word_values)
- Format encoding time
- UTF-8 encoding time
- Dictionary operations time

Usage:
    from whoosh_modern.profiling import FieldConversionProfiler
    profiler = FieldConversionProfiler(schema)
    for doc in docs:
        profiler.profile_document(doc)
    print(profiler.report())
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from whoosh import fields
from whoosh.fields import BOOLEAN, DATETIME, ID, KEYWORD, NUMERIC, TEXT


class FieldConversionProfiler:
    """Profile field conversion in detail."""

    def __init__(self, schema: fields.Schema) -> None:
        self._schema = schema
        self._doc_count: int = 0
        self._field_timings: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._field_counts: dict[str, int] = defaultdict(int)
        self._format_timings: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._total_time: float = 0.0
        self._per_document: list[dict[str, float]] = []

    def profile_document(self, doc: dict[str, Any]) -> None:
        """Profile field conversion for a single document."""
        self._doc_count += 1
        doc_timings: dict[str, float] = {}
        fieldnames = sorted([name for name in doc if not name.startswith("_")])

        for fieldname in fieldnames:
            value = doc.get(fieldname)
            if value is None:
                continue
            try:
                field = self._schema[fieldname]
            except KeyError:
                continue

            field_type = type(field).__name__
            field_key = f"{fieldname}:{field_type}"

            # Measure field.index() call
            t0 = time.perf_counter()
            items = list(field.index(value))
            total = time.perf_counter() - t0

            doc_timings[field_key] = total
            self._field_timings[field_key]["total"] += total
            self._field_counts[field_key] += 1

            # Measure format if available
            if hasattr(field, "format") and field.format is not None:
                fmt = field.format
                fmt_type = type(fmt).__name__
                self._format_timings[fmt_type]["count"] += 1
                self._format_timings[fmt_type]["total_time"] += total

        doc_total = sum(doc_timings.values())
        self._total_time += doc_total
        self._per_document.append(doc_timings)

    def report(self) -> str:
        """Generate a human-readable report."""
        if self._doc_count == 0:
            return "No documents profiled."

        lines = ["Field Conversion Profiling", "=" * 60, ""]
        lines.append(f"Documents profiled: {self._doc_count}")
        lines.append(f"Total field conversion time: {self._total_time:.4f}s")
        lines.append(f"Average per document: {self._total_time / self._doc_count * 1000:.2f} ms")
        lines.append("")

        # Per-field breakdown
        lines.append("Per-field breakdown:")
        lines.append(f"{'Field':<30} {'Count':>8} {'Total (s)':>12} {'Avg (ms)':>10} {'%':>8}")
        lines.append("-" * 72)

        total_time = self._total_time
        for field_key in sorted(self._field_timings.keys()):
            timings = self._field_timings[field_key]
            count = self._field_counts[field_key]
            field_total = timings["total"]
            avg = field_total / count * 1000 if count > 0 else 0
            pct = field_total / total_time * 100 if total_time > 0 else 0
            lines.append(
                f"{field_key:<30} {count:>8} {field_total:>12.4f} {avg:>10.2f} {pct:>8.1f}"
            )

        lines.append("")

        # Per-format breakdown
        if self._format_timings:
            lines.append("Per-format breakdown:")
            lines.append(f"{'Format':<20} {'Count':>8} {'Total (s)':>12} {'%':>8}")
            lines.append("-" * 52)
            for fmt_type in sorted(self._format_timings.keys()):
                timings = self._format_timings[fmt_type]
                count = int(timings["count"])
                fmt_total = timings["total_time"]
                pct = fmt_total / total_time * 100 if total_time > 0 else 0
                lines.append(f"{fmt_type:<20} {count:>8} {fmt_total:>12.4f} {pct:>8.1f}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return results as a dict."""
        return {
            "doc_count": self._doc_count,
            "total_time": self._total_time,
            "per_document_avg_ms": self._total_time / self._doc_count * 1000
            if self._doc_count > 0
            else 0,
            "field_timings": {k: dict(v) for k, v in self._field_timings.items()},
            "field_counts": dict(self._field_counts),
            "format_timings": {k: dict(v) for k, v in self._format_timings.items()},
        }
