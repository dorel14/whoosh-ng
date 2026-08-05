"""Full indexing pipeline profiler.

Measures per-document cost for:
- Analyzer
- Schema processing
- Field conversion
- Posting creation

Usage:
    from whoosh_modern.profiling import IndexingPipelineProfiler
    profiler = IndexingPipelineProfiler(schema)
    for doc in docs:
        profiler.profile_document(doc)
    print(profiler.report())
"""

from __future__ import annotations

import time
from typing import Any

from whoosh.fields import BOOLEAN, DATETIME, ID, KEYWORD, NUMERIC, TEXT, Schema


class IndexingPipelineProfiler:
    """Profile each stage of the indexing pipeline."""

    def __init__(self, schema: Schema) -> None:
        self._schema = schema
        self._doc_count: int = 0
        self._analyzer_time: float = 0.0
        self._schema_time: float = 0.0
        self._field_conversion_time: float = 0.0
        self._posting_creation_time: float = 0.0
        self._total_time: float = 0.0
        self._timings: list[dict[str, float]] = []

    def profile_document(self, doc: dict[str, Any]) -> None:
        """Profile indexing of a single document."""
        self._doc_count += 1
        doc_timings: dict[str, float] = {}

        # 1. Analyzer
        t0 = time.perf_counter()
        analyzed = self._analyze_document(doc)
        t1 = time.perf_counter()
        analyzer_time = t1 - t0
        doc_timings["analyzer"] = analyzer_time
        self._analyzer_time += analyzer_time

        # 2. Schema processing
        t0 = time.perf_counter()
        field_values = self._process_schema(doc, analyzed)
        t1 = time.perf_counter()
        schema_time = t1 - t0
        doc_timings["schema_processing"] = schema_time
        self._schema_time += schema_time

        # 3. Field conversion
        t0 = time.perf_counter()
        converted = self._convert_fields(field_values)
        t1 = time.perf_counter()
        field_conversion_time = t1 - t0
        doc_timings["field_conversion"] = field_conversion_time
        self._field_conversion_time += field_conversion_time

        # 4. Posting creation
        t0 = time.perf_counter()
        self._create_postings(converted)
        t1 = time.perf_counter()
        posting_creation_time = t1 - t0
        doc_timings["posting_creation"] = posting_creation_time
        self._posting_creation_time += posting_creation_time

        doc_timings["total"] = (
            analyzer_time + schema_time + field_conversion_time + posting_creation_time
        )
        self._total_time += doc_timings["total"]
        self._timings.append(doc_timings)

    def _analyze_document(self, doc: dict[str, Any]) -> dict[str, list[str]]:
        """Analyze document fields through their analyzers."""
        analyzed: dict[str, list[str]] = {}
        for fieldname, field in self._schema.items():
            if fieldname not in doc:
                continue
            value = doc[fieldname]
            if isinstance(value, str):
                analyzer = field.analyzer
                analyzed[fieldname] = list(analyzer(value))
            elif isinstance(value, list):
                analyzer = field.analyzer
                tokens = []
                for v in value:
                    tokens.extend(analyzer(v))
                analyzed[fieldname] = tokens
        return analyzed

    def _process_schema(
        self, doc: dict[str, Any], analyzed: dict[str, list[str]]
    ) -> dict[str, Any]:
        """Process document according to schema rules."""
        field_values: dict[str, Any] = {}
        for fieldname, _ in self._schema.items():
            if fieldname in analyzed:
                field_values[fieldname] = analyzed[fieldname]
            elif fieldname in doc:
                field_values[fieldname] = doc[fieldname]
        return field_values

    def _convert_fields(self, field_values: dict[str, Any]) -> dict[str, Any]:
        """Convert field values to indexable format."""
        converted: dict[str, Any] = {}
        for fieldname, value in field_values.items():
            field = self._schema[fieldname]
            if isinstance(field, (TEXT, KEYWORD)):
                if isinstance(value, list):
                    converted[fieldname] = " ".join(str(v) for v in value)
                else:
                    converted[fieldname] = str(value)
            elif isinstance(field, ID):
                converted[fieldname] = str(value)
            elif isinstance(field, NUMERIC):
                converted[fieldname] = float(value)
            elif isinstance(field, BOOLEAN):
                converted[fieldname] = bool(value)
            elif isinstance(field, DATETIME):
                converted[fieldname] = value
        return converted

    def _create_postings(self, converted: dict[str, Any]) -> None:
        """Simulate posting creation (no actual index writing)."""
        pass

    def report(self) -> str:
        """Generate a human-readable report."""
        if self._doc_count == 0:
            return "No documents profiled."

        lines = ["Indexing Pipeline Profiling", "=" * 50, ""]
        lines.append(f"Documents profiled: {self._doc_count}")
        lines.append("")

        # Overall totals
        lines.append("Overall timing:")
        lines.append(
            f"  Analyzer            : {self._analyzer_time:.4f}s "
            f"({self._analyzer_time / self._total_time * 100:.1f}%)"
        )
        lines.append(
            f"  Schema processing   : {self._schema_time:.4f}s "
            f"({self._schema_time / self._total_time * 100:.1f}%)"
        )
        lines.append(
            f"  Field conversion    : {self._field_conversion_time:.4f}s "
            f"({self._field_conversion_time / self._total_time * 100:.1f}%)"
        )
        lines.append(
            f"  Posting creation    : {self._posting_creation_time:.4f}s "
            f"({self._posting_creation_time / self._total_time * 100:.1f}%)"
        )
        lines.append(f"  Total               : {self._total_time:.4f}s")
        lines.append("")

        # Per-document averages
        lines.append("Per-document averages:")
        lines.append(
            f"  Analyzer            : {self._analyzer_time / self._doc_count * 1000:.2f} ms"
        )
        lines.append(f"  Schema processing   : {self._schema_time / self._doc_count * 1000:.2f} ms")
        lines.append(
            f"  Field conversion    : {self._field_conversion_time / self._doc_count * 1000:.2f} ms"
        )
        lines.append(
            f"  Posting creation    : {self._posting_creation_time / self._doc_count * 1000:.2f} ms"
        )
        lines.append(f"  Total               : {self._total_time / self._doc_count * 1000:.2f} ms")
        lines.append("")

        # Distribution
        if self._timings:
            totals = [t["total"] for t in self._timings]
            totals.sort()
            p50 = totals[len(totals) // 2]
            p95 = totals[int(len(totals) * 0.95)]
            p99 = totals[int(len(totals) * 0.99)]
            max_t = totals[-1]
            lines.append("Per-document total time distribution:")
            lines.append(f"  p50: {p50 * 1000:.2f} ms")
            lines.append(f"  p95: {p95 * 1000:.2f} ms")
            lines.append(f"  p99: {p99 * 1000:.2f} ms")
            lines.append(f"  max: {max_t * 1000:.2f} ms")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return results as a dict."""
        return {
            "doc_count": self._doc_count,
            "analyzer_time": self._analyzer_time,
            "schema_time": self._schema_time,
            "field_conversion_time": self._field_conversion_time,
            "posting_creation_time": self._posting_creation_time,
            "total_time": self._total_time,
            "per_document_avg_ms": self._total_time / self._doc_count * 1000
            if self._doc_count > 0
            else 0,
        }
