"""Unified pipeline profiler for Whoosh-NG.

Profiles the real indexing path in a single pass with non-overlapping categories:
- field.index() : analyzer + encoding
- pool.add() : posting pool additions
- perdocwriter.add_field() : per-document storage
- other : schema validation, boosts, etc.

Usage:
    from whoosh_modern.profiling import UnifiedPipelineProfiler
    profiler = UnifiedPipelineProfiler(writer)
    with profiler:
        for doc in docs:
            writer.add_document(**doc)
    print(profiler.report())
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any


class UnifiedPipelineProfiler:
    """Profile the full indexing path in a single pass."""

    def __init__(self, writer: Any) -> None:
        self._writer = writer
        self._patched: bool = False
        self._doc_count: int = 0
        self._total_time: float = 0.0
        self._field_index_time: float = 0.0
        self._pool_add_time: float = 0.0
        self._perdoc_time: float = 0.0
        self._other_time: float = 0.0
        self._field_counts: dict[str, int] = defaultdict(int)
        self._per_document: list[dict[str, float]] = []

    def __enter__(self) -> UnifiedPipelineProfiler:
        self._patch()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._unpatch()

    def _patch(self) -> None:
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

                    # 1. field.index() : analyzer + encoding
                    t0 = time.perf_counter()
                    fieldboost = writer._field_boost(fields, fieldname, docboost)
                    items = list(field.index(value))
                    field_index_time = time.perf_counter() - t0
                    doc_timings[f"field_index:{fieldname}"] = field_index_time
                    profiler._field_index_time += field_index_time
                    profiler._field_counts[fieldname] += len(items)

                    # 2. pool.add() : posting pool additions
                    t0 = time.perf_counter()
                    scorable = field.scorable
                    length = 0
                    for tbytes, freq, weight, vbytes in items:
                        weight *= fieldboost
                        if scorable:
                            length += freq
                        pool_add((fieldname, tbytes, docnum, weight, vbytes))
                    pool_add_time = time.perf_counter() - t0
                    doc_timings[f"pool_add:{fieldname}"] = pool_add_time
                    profiler._pool_add_time += pool_add_time

                    # 3. perdocwriter.add_field() : per-document storage
                    t0 = time.perf_counter()
                    customval = fields.get(f"_stored_{fieldname}", value)
                    sv = customval if field.stored else None
                    perdocwriter.add_field(fieldname, field, sv, length)
                    perdoc_time = time.perf_counter() - t0
                    doc_timings[f"perdoc:{fieldname}"] = perdoc_time
                    profiler._perdoc_time += perdoc_time

                    # 4. Other : column values, vector processing, etc.
                    other_time = 0.0
                    if field.separate_spelling():
                        t0 = time.perf_counter()
                        spellfield = field.spelling_fieldname(fieldname)
                        for word in field.spellable_words(value):
                            word = writer._utf8encode(word)[0]
                            pool_add((spellfield, word, 0, 1, vbytes))
                        other_time += time.perf_counter() - t0

                    vformat = field.vector
                    if vformat:
                        t0 = time.perf_counter()
                        analyzer = field.analyzer
                        vitems = vformat.word_values(value, analyzer, mode="index")
                        vitems = sorted(
                            (text, weight, vbytes) for text, _, weight, vbytes in vitems
                        )
                        perdocwriter.add_vector_items(fieldname, field, vitems)
                        other_time += time.perf_counter() - t0

                    column = field.column_type
                    if column and customval is not None:
                        t0 = time.perf_counter()
                        cv = field.to_column_value(customval)
                        perdocwriter.add_column_value(fieldname, column, cv)
                        other_time += time.perf_counter() - t0

                    if other_time > 0:
                        doc_timings[f"other:{fieldname}"] = other_time
                        profiler._other_time += other_time
            except ValueError:
                perdocwriter.cancel_doc()
                raise

            perdocwriter.finish_doc()
            writer.docnum += 1

            doc_total = time.perf_counter() - doc_start
            profiler._doc_count += 1
            profiler._total_time += doc_total
            profiler._per_document.append(doc_timings)

        writer.add_document = timed_add_document  # type: ignore[method-assign]
        self._orig_add_document = orig_add_document

    def _unpatch(self) -> None:
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

        lines = ["Unified Pipeline Profiling", "=" * 60, ""]
        lines.append(f"Documents profiled: {self._doc_count}")
        total = self._total_time
        lines.append(f"Total time: {total:.4f}s")
        lines.append(f"Average per document: {total / self._doc_count * 1000:.2f} ms")
        lines.append("")

        # Non-overlapping categories
        categories = {
            "field.index()": self._field_index_time,
            "pool.add()": self._pool_add_time,
            "perdocwriter.add_field()": self._perdoc_time,
            "other": self._other_time,
        }

        lines.append("Non-overlapping breakdown:")
        lines.append(f"{'Category':<30} {'Time (s)':>10} {'%':>8}")
        lines.append("-" * 52)
        for name, t in categories.items():
            pct = t / total * 100 if total > 0 else 0.0
            lines.append(f"  {name:<28} {t:>10.4f} {pct:>7.1f}%")

        lines.append("-" * 52)
        lines.append(f"  {'Total':<28} {total:>10.4f} {'100.0':>8}%")

        lines.append("")

        # Per-field breakdown
        lines.append("Per-field breakdown:")
        lines.append(
            f"{'Field':<20} {'Terms':>8} {'field.index()':>14} {'pool.add()':>12} {'perdoc':>10}"
        )
        lines.append("-" * 68)
        fieldnames = sorted(self._field_counts.keys())
        for fn in fieldnames:
            fi_time = sum(t.get(f"field_index:{fn}", 0.0) for t in self._per_document)
            pa_time = sum(t.get(f"pool_add:{fn}", 0.0) for t in self._per_document)
            pd_time = sum(t.get(f"perdoc:{fn}", 0.0) for t in self._per_document)
            count = self._field_counts[fn]
            lines.append(
                f"  {fn:<18} {count:>8} {fi_time * 1000:>13.2f} {pa_time * 1000:>11.2f} {pd_time * 1000:>9.2f}"
            )

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Return results as a dict."""
        total = self._total_time
        categories = {
            "field_index": self._field_index_time,
            "pool_add": self._pool_add_time,
            "perdoc": self._perdoc_time,
            "other": self._other_time,
        }
        return {
            "doc_count": self._doc_count,
            "total_time": total,
            "per_document_avg_ms": total / self._doc_count * 1000 if self._doc_count > 0 else 0,
            "categories": categories,
            "percentages": {
                k: v / total * 100 if total > 0 else 0.0 for k, v in categories.items()
            },
            "field_counts": dict(self._field_counts),
        }
