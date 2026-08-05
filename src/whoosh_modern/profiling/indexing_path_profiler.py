"""Full indexing path profiler for Whoosh-NG.

Instruments the actual indexing path:
Document → Fields → Analyzer → PostingPool

Usage:
    from whoosh_modern.profiling import IndexingPathProfiler
    profiler = IndexingPathProfiler(writer)
    for doc in docs:
        profiler.profile_document(doc)
    print(profiler.report())
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any


class IndexingPathProfiler:
    """Profile the full indexing path with fine instrumentation."""

    def __init__(self, writer: Any) -> None:
        self._writer = writer
        self._doc_count: int = 0
        self._term_count: int = 0
        self._timings: dict[str, float] = defaultdict(float)
        self._counts: dict[str, int] = defaultdict(int)
        self._per_document: list[dict[str, float]] = []
        self._patched: bool = False

    def __enter__(self) -> IndexingPathProfiler:
        self._patch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._unpatch()

    def _patch(self) -> None:
        """Monkey-patch the writer's add_document method."""
        if self._patched:
            return
        self._patched = True

        writer = self._writer
        profiler = self

        orig_add_document = writer.add_document

        def timed_add_document(**fields):
            doc_start = time.perf_counter()
            doc_timings: dict[str, float] = {}

            schema = writer.schema
            docboost = writer._doc_boost(fields)
            fieldnames = sorted([name for name in fields if not name.startswith("_")])
            writer._check_fields(schema, fieldnames)

            perdocwriter = writer.perdocwriter
            pool_add = writer.pool.add
            docnum = writer.docnum

            perdocwriter.start_doc(docnum)
            try:
                for fieldname in fieldnames:
                    value = fields.get(fieldname)
                    if value is None:
                        continue
                    field = schema[fieldname]

                    # Measure field.index() - includes analyzer + format encoding
                    t0 = time.perf_counter()
                    fieldboost = writer._field_boost(fields, fieldname, docboost)
                    items = list(field.index(value))
                    field_index_time = time.perf_counter() - t0

                    field_key = f"field_index:{fieldname}"
                    doc_timings[field_key] = doc_timings.get(field_key, 0.0) + field_index_time
                    profiler._timings[field_key] += field_index_time
                    profiler._counts[field_key] += len(items)

                    # Measure pool.add() for each term
                    t0 = time.perf_counter()
                    scorable = field.scorable
                    length = 0
                    for tbytes, freq, weight, vbytes in items:
                        weight *= fieldboost
                        if scorable:
                            length += freq
                        pool_add((fieldname, tbytes, docnum, weight, vbytes))
                    pool_add_time = time.perf_counter() - t0

                    pool_key = f"pool_add:{fieldname}"
                    doc_timings[pool_key] = doc_timings.get(pool_key, 0.0) + pool_add_time
                    profiler._timings[pool_key] += pool_add_time
                    profiler._counts[pool_key] += len(items)

                    # Measure per-doc field storage
                    t0 = time.perf_counter()
                    customval = fields.get(f"_stored_{fieldname}", value)
                    sv = customval if field.stored else None
                    perdocwriter.add_field(fieldname, field, sv, length)
                    perdoc_time = time.perf_counter() - t0

                    perdoc_key = f"perdoc_field:{fieldname}"
                    doc_timings[perdoc_key] = doc_timings.get(perdoc_key, 0.0) + perdoc_time
                    profiler._timings[perdoc_key] += perdoc_time
                    profiler._counts[perdoc_key] += 1

                    # Measure column value conversion
                    column = field.column_type
                    if column and customval is not None:
                        t0 = time.perf_counter()
                        cv = field.to_column_value(customval)
                        perdocwriter.add_column_value(fieldname, column, cv)
                        column_time = time.perf_counter() - t0

                        column_key = f"column:{fieldname}"
                        doc_timings[column_key] = doc_timings.get(column_key, 0.0) + column_time
                        profiler._timings[column_key] += column_time
                        profiler._counts[column_key] += 1
            except ValueError:
                perdocwriter.cancel_doc()
                raise

            perdocwriter.finish_doc()
            writer.docnum += 1

            doc_total = time.perf_counter() - doc_start
            profiler._doc_count += 1
            profiler._term_count += sum(
                profiler._counts.get(f"field_index:{fn}", 0) for fn in fieldnames
            )
            profiler._timings["total"] += doc_total
            profiler._per_document.append(doc_timings)

        writer.add_document = timed_add_document  # type: ignore[method-assign]
        self._orig_add_document = orig_add_document

    def _unpatch(self) -> None:
        """Restore original add_document method."""
        if self._patched:
            self._writer.add_document = self._orig_add_document  # type: ignore[method-assign]
            self._patched = False

    def profile_document(self, doc: dict[str, Any]) -> None:
        """Profile a single document (uses patched add_document)."""
        self._writer.add_document(**doc)

    def report(self) -> str:
        """Generate a human-readable report."""
        if self._doc_count == 0:
            return "No documents profiled."

        lines = ["Indexing Path Profiling", "=" * 60, ""]
        lines.append(f"Documents profiled: {self._doc_count}")
        total = self._timings["total"]
        lines.append(f"Total time: {total:.4f}s")
        lines.append(f"Average per document: {total / self._doc_count * 1000:.2f} ms")
        lines.append("")

        # Aggregate by category
        categories: dict[str, float] = defaultdict(float)
        for key, t in self._timings.items():
            if key == "total":
                continue
            category = key.split(":")[0]
            categories[category] += t

        lines.append("Overall breakdown:")
        labels = {
            "field_index": "field.index() (analyzer + encoding)",
            "pool_add": "PostingPool.add()",
            "perdoc_field": "Per-doc storage",
            "column": "Column values",
        }
        for key, label in labels.items():
            t = categories.get(key, 0.0)
            pct = t / total * 100 if total > 0 else 0.0
            lines.append(f"  {label:<35} {t:>10.4f}s  ({pct:>6.1f}%)")

        # Uncategorized
        uncategorized = sum(v for k, v in categories.items() if k not in labels)
        pct = uncategorized / total * 100 if total > 0 else 0.0
        lines.append(
            f"  {'Other (schema/boost/validation)':<35} {uncategorized:>10.4f}s  ({pct:>6.1f}%)"
        )

        lines.append("")

        # Per-field breakdown
        lines.append("Per-field breakdown:")
        fieldnames = sorted(
            set(key.split(":")[1] for key in self._timings if ":" in key and key != "total")
        )
        for fn in fieldnames:
            field_total = sum(self._timings.get(f"{cat}:{fn}", 0.0) for cat in categories)
            term_count = self._counts.get(f"field_index:{fn}", 0)
            lines.append(f"  {fn:<20} {term_count:>8} terms  {field_total * 1000:>10.2f} ms")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return results as a dict."""
        total = self._timings["total"]
        categories: dict[str, float] = defaultdict(float)
        for key, t in self._timings.items():
            if key == "total":
                continue
            category = key.split(":")[0]
            categories[category] += t

        return {
            "doc_count": self._doc_count,
            "term_count": self._term_count,
            "total_time": total,
            "per_document_avg_ms": total / self._doc_count * 1000 if self._doc_count > 0 else 0,
            "breakdown": {
                k: {"time": v, "pct": v / total * 100 if total > 0 else 0}
                for k, v in categories.items()
            },
        }
