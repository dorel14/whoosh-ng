"""Field transformation profiler for Whoosh-NG.

Instruments field methods:
- field.index()
- field.prepare()
- field.to_bytes()
- field.clean()

Usage:
    from whoosh_modern.profiling import FieldTransformationProfiler
    profiler = FieldTransformationProfiler(schema)
    for doc in docs:
        profiler.profile_document(doc)
    print(profiler.report())
"""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import suppress
from typing import Any


class FieldTransformationProfiler:
    """Profile field transformations in detail."""

    def __init__(self, schema: Any) -> None:
        self._schema = schema
        self._doc_count: int = 0
        self._field_timings: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._field_counts: dict[str, int] = defaultdict(int)
        self._total_time: float = 0.0
        self._per_document: list[dict[str, float]] = []

    def profile_document(self, doc: dict[str, Any]) -> None:
        """Profile field transformations for a single document."""
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

            # Measure field.index()
            t0 = time.perf_counter()
            try:
                items = list(field.index(value))
            except Exception:
                items = []
            index_time = time.perf_counter() - t0

            doc_timings[f"{field_key}:index"] = index_time
            self._field_timings[field_key]["index"] += index_time
            self._field_counts[field_key] += len(items)

            # Measure field.prepare() if available
            prepare_time = 0.0
            if hasattr(field, "prepare"):
                t0 = time.perf_counter()
                with suppress(Exception):
                    field.prepare(value)
                prepare_time = time.perf_counter() - t0
                doc_timings[f"{field_key}:prepare"] = prepare_time
                self._field_timings[field_key]["prepare"] += prepare_time

            # Measure field.to_bytes() if available
            to_bytes_time = 0.0
            if hasattr(field, "to_bytes"):
                t0 = time.perf_counter()
                with suppress(Exception):
                    field.to_bytes(value)
                to_bytes_time = time.perf_counter() - t0
                doc_timings[f"{field_key}:to_bytes"] = to_bytes_time
                self._field_timings[field_key]["to_bytes"] += to_bytes_time

            # Measure field.clean() if available
            clean_time = 0.0
            if hasattr(field, "clean"):
                t0 = time.perf_counter()
                with suppress(Exception):
                    field.clean(value)
                clean_time = time.perf_counter() - t0
                doc_timings[f"{field_key}:clean"] = clean_time
                self._field_timings[field_key]["clean"] += clean_time

        doc_total = sum(doc_timings.values())
        self._total_time += doc_total
        self._per_document.append(doc_timings)

    def report(self) -> str:
        """Generate a human-readable report."""
        if self._doc_count == 0:
            return "No documents profiled."

        lines = ["Field Transformation Profiling", "=" * 60, ""]
        lines.append(f"Documents profiled: {self._doc_count}")
        lines.append(f"Total field transformation time: {self._total_time:.4f}s")
        lines.append(f"Average per document: {self._total_time / self._doc_count * 1000:.2f} ms")
        lines.append("")

        # Overall breakdown
        categories: defaultdict[str, float] = defaultdict(float)
        for _, timings in self._field_timings.items():
            for method, t in timings.items():
                categories[method] += t

        lines.append("Overall breakdown:")
        total = self._total_time
        for method in ["index", "prepare", "to_bytes", "clean"]:
            t = categories.get(method, 0.0)
            pct = t / total * 100 if total > 0 else 0.0
            lines.append(f"  {method:<15} {t:>10.4f}s  ({pct:>6.1f}%)")

        lines.append("")

        # Per-field breakdown
        lines.append("Per-field breakdown:")
        lines.append(
            f"{'Field':<30} {'Index (ms)':>12} {'Prepare (ms)':>14} "
            f"{'To_bytes (ms)':>14} {'Clean (ms)':>12}"
        )
        lines.append("-" * 86)

        for _field_key in sorted(self._field_timings.keys()):
            timings = self._field_timings[_field_key]
            count = self._field_counts[_field_key]
            avg_index = timings.get("index", 0.0) / count * 1000 if count > 0 else 0
            avg_prepare = timings.get("prepare", 0.0) / count * 1000 if count > 0 else 0
            avg_to_bytes = timings.get("to_bytes", 0.0) / count * 1000 if count > 0 else 0
            avg_clean = timings.get("clean", 0.0) / count * 1000 if count > 0 else 0
            lines.append(
                f"{_field_key:<30} {avg_index:>12.2f} {avg_prepare:>14.2f} "
                f"{avg_to_bytes:>14.2f} {avg_clean:>12.2f}"
            )

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return results as a dict."""
        categories: defaultdict[str, float] = defaultdict(float)
        for _, timings in self._field_timings.items():
            for method, t in timings.items():
                categories[method] += t

        return {
            "doc_count": self._doc_count,
            "total_time": self._total_time,
            "per_document_avg_ms": self._total_time / self._doc_count * 1000
            if self._doc_count > 0
            else 0,
            "categories": dict(categories),
            "field_timings": {k: dict(v) for k, v in self._field_timings.items()},
            "field_counts": dict(self._field_counts),
        }
