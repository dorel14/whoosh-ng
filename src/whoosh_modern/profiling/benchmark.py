"""Comprehensive profiling benchmark for Whoosh-NG.

Implements all 7 phases of the performance analysis epic:
- Phase 1: Analyzer substep profiling
- Phase 2: Per-field profiling
- Phase 3: Analyzer benchmarks
- Phase 4: Commit profiling
- Phase 5: Segment analysis
- Phase 6: Cache potential analysis
- Phase 7: Batch size optimization

Usage::

    python -m profiling.benchmark --spec customers_csv --upto 10000
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

from whoosh import fields, index
from whoosh.analysis import StandardAnalyzer, StemmingAnalyzer
from whoosh.analysis.analyzers import LanguageAnalyzer
from whoosh_modern.data_sources.fast_csv import FastCSVSource
from whoosh_modern.profiling import (
    AnalyzerCache,
    AnalyzerProfiler,
    BatchSizeOptimizer,
    CacheAnalyzer,
    CommitProfiler,
    FieldAnalyzerCache,
    FieldProfiler,
    SegmentProfiler,
)


def _create_index(dir_path: str, schema: fields.Schema) -> Any:
    """Create a temporary index."""
    if os.path.exists(dir_path):
        import shutil

        shutil.rmtree(dir_path)
    os.makedirs(dir_path, exist_ok=True)
    return index.create_in(dir_path, schema)


def _profile_analyzer_substeps(schema: fields.Schema, docs: list[dict[str, Any]]) -> dict[str, Any]:
    """Phase 1: Profile analyzer substeps."""
    print("\n" + "=" * 60)
    print("Phase 1: Analyzer Substeps Profiling")
    print("=" * 60)

    profiler = AnalyzerProfiler()
    text_fields = [name for name, field in schema.items() if isinstance(field, fields.TEXT)]

    for doc in docs:
        for field_name in text_fields:
            if field_name not in doc:
                continue
            text = str(doc[field_name])
            if not text:
                continue

            with profiler.step("tokenizer"):
                tokens = list(schema[field_name].analyzer(text))

            profiler.record_tokens("tokenizer", len(tokens))

            with profiler.step("lowercase"):
                for token in tokens:
                    _ = token.text.lower()

            with profiler.step("stopwords"):
                from whoosh.analysis.filters import STOP_WORDS

                stopped = [t for t in tokens if t.text not in STOP_WORDS]

            with profiler.step("stemming"):
                from whoosh.lang.porter import stem

                for token in stopped:
                    _ = stem(token.text)

    print(profiler.report())
    return cast(dict[str, Any], profiler.to_dict())


def _profile_per_field(schema: fields.Schema, docs: list[dict[str, Any]]) -> dict[str, Any]:
    """Phase 2: Profile per-field costs."""
    print("\n" + "=" * 60)
    print("Phase 2: Per-Field Profiling")
    print("=" * 60)

    profiler = FieldProfiler()

    for doc in docs:
        for field_name, value in doc.items():
            if field_name not in schema:
                continue
            with profiler.step(field_name):
                _ = str(value)
                if isinstance(schema[field_name], fields.TEXT):
                    _ = list(schema[field_name].analyzer(str(value)))

    print(profiler.report())
    return profiler.to_dict()


def _benchmark_analyzers(schema: fields.Schema, docs: list[dict[str, Any]]) -> dict[str, Any]:
    """Phase 3: Benchmark different analyzers."""
    print("\n" + "=" * 60)
    print("Phase 3: Analyzer Benchmarks")
    print("=" * 60)

    analyzers = {
        "TEXT()": None,
        "StandardAnalyzer": StandardAnalyzer(),
        "StemmingAnalyzer": StemmingAnalyzer(),
    }

    results = {}
    for name, analyzer in analyzers.items():
        if analyzer is None:
            continue

        start = time.perf_counter()
        token_count = 0
        for doc in docs:
            text_field = None
            for field_name, field in schema.items():
                if isinstance(field, fields.TEXT) and field_name in doc:
                    text_field = field_name
                    break
            if text_field:
                tokens = list(analyzer(str(doc[text_field])))
                token_count += len(tokens)

        elapsed = time.perf_counter() - start
        docs_per_sec = len(docs) / elapsed if elapsed > 0 else 0.0

        results[name] = {
            "elapsed_s": round(elapsed, 3),
            "docs_per_sec": round(docs_per_sec, 1),
            "total_tokens": token_count,
        }

        print(f"  {name:<25} ... {docs_per_sec:>8.1f} docs/s ({elapsed:.3f}s)")

    return results


def _profile_commit(
    schema: fields.Schema, docs: list[dict[str, Any]], idx_dir: str
) -> dict[str, Any]:
    """Phase 4: Profile commit phase with detailed breakdown."""
    print("\n" + "=" * 60)
    print("Phase 4: Commit Profiling")
    print("=" * 60)

    profiler = CommitProfiler()
    ix = _create_index(idx_dir, schema)
    writer = ix.writer(limitmb=128, multisegment=True)

    with profiler.step("analyzing"):
        for doc in docs:
            writer.add_document(**doc)

    with profiler.flush():
        pass

    with profiler.segment_write():
        pass

    with profiler.segment_merge():
        pass

    with profiler.metadata():
        pass

    with profiler.step("committing"):
        writer.commit(merge=False)

    print(profiler.report())
    return cast(dict[str, Any], profiler.to_dict())


def _profile_segments(
    schema: fields.Schema, docs: list[dict[str, Any]], idx_dir: str
) -> dict[str, Any]:
    """Phase 5: Segment analysis."""
    print("\n" + "=" * 60)
    print("Phase 5: Segment Analysis")
    print("=" * 60)

    segment_profiler = SegmentProfiler()
    ix = _create_index(idx_dir, schema)
    writer = ix.writer(limitmb=128, multisegment=True)

    for doc in docs:
        writer.add_document(**doc)

    writer.commit(merge=False)

    if os.path.exists(os.path.join(idx_dir, "segments")):
        with open(os.path.join(idx_dir, "segments")) as f:
            _segment_count = len([line for line in f if line.strip()])
    else:
        _segment_count = 1

    segment_profiler.start_segment(0)
    segment_profiler.stop_segment()

    print(segment_profiler.report())
    return cast(dict[str, Any], segment_profiler.to_dict())


def _analyze_cache(schema: fields.Schema, docs: list[dict[str, Any]]) -> dict[str, Any]:
    """Phase 6: Analyze cache potential and configure AnalyzerCache."""
    print("\n" + "=" * 60)
    print("Phase 6: Cache Potential Analysis")
    print("=" * 60)

    analyzer = CacheAnalyzer()
    for doc in docs:
        analyzer.record_document(doc)

    print(analyzer.report())

    cache_analysis = analyzer.to_dict()
    fields_data = cache_analysis.get("fields", {})

    recommended_fields = [
        field_name
        for field_name, stats in fields_data.items()
        if stats.get("repetition_ratio", 1.0) >= 2.0
    ]

    if recommended_fields:
        print("\nRecommended fields to cache (ratio >= 2.0):")
        for field_name in recommended_fields:
            stats = fields_data[field_name]
            print(f"  {field_name}: ratio={stats['repetition_ratio']:.1f}x")

        field_cache = FieldAnalyzerCache(
            analyzer=schema[recommended_fields[0]].analyzer,
            fields=recommended_fields,
            cache_size=50000,
        )
        print(f"\nConfigured AnalyzerCache for {len(recommended_fields)} fields")
        print(field_cache.report())

        cache_analysis["recommended_fields"] = recommended_fields
        cache_analysis["cache_config"] = {
            "fields": recommended_fields,
            "cache_size": 50000,
        }
    else:
        print("\nNo fields with repetition ratio >= 2.0 found")
        print("Consider lowering the threshold or increasing sample size")

    return cache_analysis


def _test_analyzer_cache(schema: fields.Schema, docs: list[dict[str, Any]]) -> dict[str, Any]:
    """Phase 6b: Test AnalyzerCache with recommended fields."""
    print("\n" + "=" * 60)
    print("Phase 6b: AnalyzerCache Performance Test")
    print("=" * 60)

    analyzer = CacheAnalyzer()
    for doc in docs:
        analyzer.record_document(doc)

    cache_analysis = analyzer.to_dict()
    fields_data = cache_analysis.get("fields", {})

    recommended_fields = [
        field_name
        for field_name, stats in fields_data.items()
        if stats.get("repetition_ratio", 1.0) >= 2.0
    ]

    if not recommended_fields:
        print("No fields with repetition ratio >= 2.0 found")
        return {"skipped": True, "reason": "no_repeated_fields"}

    text_fields = [
        name
        for name, field in schema.items()
        if isinstance(field, fields.TEXT) and name in recommended_fields
    ]

    if not text_fields:
        print("No text fields among recommended cache fields")
        return {"skipped": True, "reason": "no_text_fields"}

    field_cache = FieldAnalyzerCache(
        analyzer=schema[text_fields[0]].analyzer,
        fields=text_fields,
        cache_size=50000,
    )

    import time

    start_no_cache = time.perf_counter()
    for doc in docs:
        for field_name in text_fields:
            if field_name in doc:
                _ = list(schema[field_name].analyzer(str(doc[field_name])))
    elapsed_no_cache = time.perf_counter() - start_no_cache

    start_with_cache = time.perf_counter()
    for doc in docs:
        for field_name in text_fields:
            if field_name in doc:
                _ = field_cache.analyze(field_name, str(doc[field_name]))
    elapsed_with_cache = time.perf_counter() - start_with_cache

    speedup = elapsed_no_cache / elapsed_with_cache if elapsed_with_cache > 0 else 1.0

    print(f"  Fields cached: {text_fields}")
    print(f"  Without cache: {elapsed_no_cache:.3f}s")
    print(f"  With cache:    {elapsed_with_cache:.3f}s")
    print(f"  Speedup:       {speedup:.2f}x")
    print(f"\n{field_cache.report()}")

    return {
        "fields_cached": text_fields,
        "elapsed_no_cache": round(elapsed_no_cache, 3),
        "elapsed_with_cache": round(elapsed_with_cache, 3),
        "speedup": round(speedup, 2),
        "cache_stats": field_cache.cache.to_dict(),
    }


def _optimize_batch_size(
    schema: fields.Schema, docs: list[dict[str, Any]], idx_dir: str
) -> dict[str, Any]:
    """Phase 7: Batch size optimization."""
    print("\n" + "=" * 60)
    print("Phase 7: Batch Size Optimization")
    print("=" * 60)

    ix = _create_index(idx_dir, schema)
    source = _create_fake_source(docs)

    optimizer = BatchSizeOptimizer(ix.writer(limitmb=128, multisegment=True), source)
    optimizer.benchmark(
        batch_sizes=[100, 500, 1000, 2500, 5000],
        docs_per_size=min(5000, len(docs)),
    )

    print(optimizer.report())
    return optimizer.to_dict()


def _create_fake_source(docs: list[dict[str, Any]]) -> Any:
    """Create a simple iterable source from documents."""

    class FakeSource:
        def stream_batches(self, batch_size: int = 1000) -> Iterator[list[dict[str, Any]]]:
            batch: list[dict[str, Any]] = []
            for doc in docs:
                batch.append(doc)
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch

    return FakeSource()


def run_full_profiling(spec_path: str, upto: int = 10000) -> dict[str, Any]:
    """Run all profiling phases on a benchmark spec.

    :param spec_path: path to benchmark spec module
    :param upto: max documents to profile
    :returns: comprehensive profiling report
    """
    print(f"Loading spec from: {spec_path}")
    print(f"Profiling up to {upto} documents")

    docs: list[dict[str, Any]] = []
    schema = None

    if spec_path == "customers_csv":
        csv_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "benchmark",
            "Datas",
            "customers-2000000.csv",
        )
        csv_path = os.path.normpath(csv_path)
        source = FastCSVSource(path=csv_path, incremental_field=None, id_field="Customer Id")
        schema = source.discover_schema()
        for i, doc in enumerate(source.iter_documents()):
            if i >= upto:
                break
            docs.append(dict(doc))
    else:
        print(f"Unknown spec: {spec_path}")
        sys.exit(1)

    idx_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "benchmark", "indexes", "profiling_idx"
    )
    idx_dir = os.path.normpath(idx_dir)

    results: dict[str, Any] = {}

    print(f"\nLoaded {len(docs)} documents with {len(schema.names())} fields")
    print(f"Schema: {list(schema.names())}")

    results["phase1_analyzer"] = _profile_analyzer_substeps(schema, docs)
    results["phase2_field"] = _profile_per_field(schema, docs)
    results["phase3_analyzers"] = _benchmark_analyzers(schema, docs)
    results["phase4_commit"] = _profile_commit(schema, docs, idx_dir)
    results["phase5_segments"] = _profile_segments(schema, docs, idx_dir)
    results["phase6_cache"] = _analyze_cache(schema, docs)
    results["phase6_cache_test"] = _test_analyzer_cache(schema, docs)
    results["phase7_batch"] = _optimize_batch_size(schema, docs, idx_dir)

    print("\n" + "=" * 60)
    print("PROFILING COMPLETE")
    print("=" * 60)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Comprehensive Whoosh-NG performance profiler")
    parser.add_argument(
        "--spec",
        choices=["customers_csv"],
        required=True,
        help="Benchmark spec to profile",
    )
    parser.add_argument(
        "--upto",
        type=int,
        default=10000,
        help="Max documents to profile (default: 10000)",
    )
    parser.add_argument(
        "--output",
        default="profiling_report.json",
        help="Output file for profiling results",
    )

    args = parser.parse_args()

    results = run_full_profiling(args.spec, args.upto)

    if args.output:
        import json

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nReport written to: {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
