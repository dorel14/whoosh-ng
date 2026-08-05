# Benchmark CLI entry point for Whoosh-NG
# Usage:
#   python -m benchmark --help
#   python -m benchmark --spec reuters --index --search --report csv
#   python -m benchmark --spec dictionary --index --report json
#   python -m benchmark --spec sqlsource  (runs pytest-benchmark style specs)

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

from whoosh import index, qparser, query, scoring
from whoosh.support.bench import Spec


def _is_pytest_benchmark_spec(mod) -> bool:
    """Return True if the module contains pytest-benchmark style test classes."""
    for attr in dir(mod):
        obj = getattr(mod, attr)
        if not isinstance(obj, type):
            continue
        if obj.__module__ != mod.__name__:
            continue
        for name in dir(obj):
            if name.startswith("benchmark_"):
                return True
    return False


def _has_spec_class(mod) -> bool:
    """Return True if the module contains a Spec subclass (excluding Spec itself)."""
    for attr in dir(mod):
        obj = getattr(mod, attr)
        if isinstance(obj, type) and issubclass(obj, Spec) and obj is not Spec:
            return True
    return False


def _available_specs() -> list[str]:
    # Lazy import of benchmark specs to avoid heavy imports at startup.
    specs: list[str] = []
    pkg = __package__
    import importlib.util

    bench_dir = os.path.dirname(__file__)
    for filename in os.listdir(bench_dir):
        if filename.endswith(".py") and filename not in {
            "__init__.py",
            "__main__.py",
            "reporting.py",
        }:
            name = filename[:-3]
            path = os.path.join(bench_dir, filename)
            spec = importlib.util.spec_from_file_location(f"{pkg}.{name}", path)
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception:
                continue
            if _has_spec_class(mod) or _is_pytest_benchmark_spec(mod):
                specs.append(name)
    return sorted(specs)


def _run_pytest_spec(
    spec_name: str,
    extra_args: list[str],
    report: str = "none",
    report_path: str = "benchmark_report",
) -> int:
    """Run a pytest-benchmark style spec via pytest and optionally generate a report."""
    import json
    import tempfile

    import pytest

    bench_dir = os.path.dirname(os.path.abspath(__file__))
    spec_file = os.path.join(bench_dir, f"{spec_name}.py")
    if not os.path.exists(spec_file):
        print(f"Spec file not found: {spec_file}", file=sys.stderr)
        return 1

    json_path = None
    if report != "none":
        fd, json_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        extra_args = extra_args + ["--benchmark-json", json_path]

    pytest_args = [
        spec_file,
        "--benchmark-only",
        "-W",
        "ignore::DeprecationWarning",
        "--tb=short",
        "--override-ini=norecursedirs=",
        "--override-ini=testpaths=benchmark",
        "--override-ini=python_files=benchmark_*.py",
        "--override-ini=python_classes=Benchmark*",
        "--override-ini=python_functions=benchmark_*",
        "--no-cov",
    ] + extra_args
    result = pytest.main(pytest_args)

    if report != "none" and json_path and os.path.exists(json_path):
        from .reporting import BenchmarkReport, BenchmarkResult

        with open(json_path, encoding="utf-8") as f:
            raw = json.load(f)

        import contextlib

        with contextlib.suppress(OSError):
            os.unlink(json_path)

        report_obj = BenchmarkReport(title=f"whoosh-{spec_name}")
        benchmarks = raw.get("benchmarks", [])
        for bench in benchmarks:
            name = bench.get("name", spec_name)
            stats = bench.get("stats", {})
            mean_s = stats.get("mean", 0) or 0
            min_s = stats.get("min", 0) or 0
            max_s = stats.get("max", 0) or 0
            mean_ns = mean_s * 1e9
            report_obj.add(
                BenchmarkResult(
                    name=name,
                    category="benchmark",
                    metric="mean_time_ns",
                    value=mean_ns,
                    unit="ns",
                )
            )
            report_obj.add(
                BenchmarkResult(
                    name=name,
                    category="benchmark",
                    metric="min_time_ns",
                    value=min_s * 1e9,
                    unit="ns",
                )
            )
            report_obj.add(
                BenchmarkResult(
                    name=name,
                    category="benchmark",
                    metric="max_time_ns",
                    value=max_s * 1e9,
                    unit="ns",
                )
            )

        ext = report
        out = f"{report_path}.{ext}"
        if ext == "csv":
            report_obj.to_csv(out)
        else:
            report_obj.to_json(out)
        print(f"Report written to {out}")
    return result


def _run_indexing(spec, options) -> tuple[int, float]:
    """Run indexing benchmark and return (doc_count, elapsed_seconds)."""
    schema = spec.whoosh_schema()
    idx_dir = spec.index_dir()

    if os.path.exists(idx_dir):
        shutil.rmtree(idx_dir)
    os.makedirs(idx_dir, exist_ok=True)

    use_profiling = getattr(options, "profile", False)
    batch_size = int(getattr(options, "batch_size", 0) or 0)
    skip = int(options.skip)
    upto = int(options.upto) if options.upto else 0

    if use_profiling:
        from whoosh_modern.profiling import CommitProfilerV2, IndexProfiler

        profiler = IndexProfiler()
        profiler.__enter__()
        commit_profiler = CommitProfilerV2(collect_term_stats=True)

    ix = index.create_in(idx_dir, schema)
    start = time.perf_counter()
    count = 0

    if use_profiling:
        if batch_size > 0:
            count = _run_batch_indexing_with_profiling(
                ix, spec, options, profiler, commit_profiler, batch_size, skip, upto
            )
        else:
            count = _run_single_doc_indexing_with_profiling(
                ix, spec, options, profiler, commit_profiler, skip, upto
            )

        profiler.add_documents(count)
        profiler.__exit__(None, None, None)
        print(profiler.report())
        if commit_profiler is not None:
            print(commit_profiler.report())
    elif batch_size > 0:
        count = _run_batch_indexing(ix, spec, options, batch_size, skip, upto)
    else:
        count = _run_single_doc_indexing(ix, spec, options, skip, upto)

    elapsed = time.perf_counter() - start
    print(f"Indexed {count} docs in {elapsed:.3f}s ({count / elapsed:.1f} docs/s)")
    return count, elapsed


def _run_batch_indexing_with_profiling(
    ix, spec, options, profiler, commit_profiler, batch_size, skip, upto
) -> int:
    from whoosh_modern.indexing import BatchIndexWriter

    count = 0
    with profiler.step("reading"):
        batches = list(spec.batches(batch_size))

    writer = BatchIndexWriter(
        ix,
        batch_size=batch_size,
        limitmb=options.limitmb,
        commit_every=options.progress_every if options.progress_every else None,
        multisegment=options.merge == 0,
        callback=commit_profiler.callback if commit_profiler else None,
        commit_profiler=commit_profiler,
    )
    with profiler.step("analyzing"):
        for batch in batches:
            if skip > 0:
                skip -= len(batch)
                if skip < 0:
                    batch = batch[-skip:]
                    skip = 0
                if not batch:
                    continue
            if upto and count >= upto:
                break
            added = writer.add_batch(batch)
            count += added
            if options.progress_every and count % int(options.progress_every) == 0:
                print(f"  ... {count} docs indexed")
    with profiler.step("committing"):
        writer.close()
    return count


def _run_single_doc_indexing_with_profiling(
    ix, spec, options, profiler, commit_profiler, skip, upto
) -> int:
    count = 0
    with profiler.step("reading"):
        docs = list(spec.documents())

    writer = ix.writer(
        limitmb=options.limitmb,
        procs=options.procs,
        multisegment=options.merge == 0,
    )
    with profiler.step("analyzing"):
        for doc in docs:
            if skip > 0:
                skip -= 1
                continue
            writer.add_document(**doc)
            count += 1
            if upto and count >= upto:
                break
    with profiler.step("committing"):
        writer.commit(
            merge=options.merge == 1,
            callback=commit_profiler.callback if commit_profiler else None,
        )
    return count


def _run_batch_indexing(ix, spec, options, batch_size, skip, upto) -> int:
    from whoosh_modern.indexing import BatchIndexWriter

    count = 0
    with BatchIndexWriter(
        ix,
        batch_size=batch_size,
        limitmb=options.limitmb,
        commit_every=options.progress_every if options.progress_every else None,
        multisegment=options.merge == 0,
    ) as writer:
        for batch in spec.batches(batch_size):
            if skip > 0:
                skip -= len(batch)
                if skip < 0:
                    batch = batch[-skip:]
                    skip = 0
                if not batch:
                    continue
            if upto and count >= upto:
                break
            added = writer.add_batch(batch)
            count += added
            if options.progress_every and count % int(options.progress_every) == 0:
                print(f"  ... {count} docs indexed")
    return count


def _run_single_doc_indexing(ix, spec, options, skip, upto) -> int:
    count = 0
    writer = ix.writer(
        limitmb=options.limitmb,
        procs=options.procs,
        multisegment=options.merge == 0,
    )
    for doc in spec.documents():
        if skip > 0:
            skip -= 1
            continue
        writer.add_document(**doc)
        count += 1
        if upto and count >= upto:
            break
        if options.progress_every and count % int(options.progress_every) == 0:
            print(f"  ... {count} docs indexed")
    writer.commit(merge=options.merge == 1)
    return count


def _run_searching(spec, options) -> tuple[int, float]:
    """Run searching benchmark and return (result_count, elapsed_seconds)."""
    bench_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(bench_dir)
    idx_dir = os.path.join(project_root, "benchmark", "indexes", f"{spec.name}_index")
    if not os.path.exists(idx_dir):
        print(f"Index not found: {idx_dir}. Run with --index first.", file=sys.stderr)
        return 0, 0.0

    ix = index.open_dir(idx_dir)
    searcher = ix.searcher(weighting=scoring.PL2())
    parser = qparser.QueryParser(spec.main_field, schema=ix.schema)

    qstring = " ".join(spec.args) if spec.args else spec.default_query
    start = time.perf_counter()
    q = parser.parse(qstring)
    results = searcher.search(q, limit=options.limit)
    elapsed = time.perf_counter() - start

    count = len(results)
    print(f"Search '{qstring}': {count} results in {elapsed:.4f}s")
    for i, hit in enumerate(results):
        if i >= options.limit:
            break
        print(f"  {i + 1}. {hit.fields().get(spec.headline_field, '')}")

    searcher.close()
    return count, elapsed


def _run_all(args: argparse.Namespace) -> int:
    """Run all benchmark specs sequentially."""
    available = _available_specs()
    print(f"Running {len(available)} benchmarks...\n")
    errors = 0
    for spec_name in available:
        print(f"{'=' * 60}")
        print(f"Running: {spec_name}")
        print(f"{'=' * 60}")
        filtered = [a for a in sys.argv[1:] if a != "--all"]
        ret = main(["--spec", spec_name, *filtered])
        if ret != 0:
            errors += 1
        print()
    print(f"Done. {len(available) - errors}/{len(available)} succeeded.")
    return 1 if errors else 0


def main(argv: Sequence[str] | None = None) -> int:
    available = _available_specs()
    parser = argparse.ArgumentParser(
        prog="python -m benchmark", description="Whoosh-NG benchmark runner"
    )
    parser.add_argument(
        "--spec",
        choices=available,
        required=False,
        help="Benchmark spec to run (e.g. reuters, dictionary, sqlsource)",
    )
    parser.add_argument("--index", action="store_true", help="Run indexing benchmark")
    parser.add_argument("--search", action="store_true", help="Run querying benchmark")
    parser.add_argument("--ranking", action="store_true", help="Run ranking benchmark")
    parser.add_argument(
        "--dir",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Working directory for index/data",
    )
    parser.add_argument(
        "--report", choices=["csv", "json", "none"], default="none", help="Report format"
    )
    parser.add_argument(
        "--report-path", default="benchmark_report", help="Report file path (without extension)"
    )
    parser.add_argument("--limit", type=int, default=10, help="Max search results to retrieve")
    parser.add_argument("--procs", type=int, default=0, help="Number of processors for indexing")
    parser.add_argument(
        "--limitmb", type=int, default=128, help="Max memory usage per writer in MB"
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=0,
        help="Print progress message every N docs (0=disable)",
    )
    parser.add_argument("--merge", default=1, help="Merge policy (1=SMALL, 0=none)")
    parser.add_argument("--chunk", default=0, help="Chunk size for indexing progress")
    parser.add_argument("--skip", default="1", help="Initial docs to skip (default: 1)")
    parser.add_argument("--upto", default=0, help="Maximum docs to index (0=unlimited)")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=0,
        help="Commit writer every N docs (0=disable batch commits)",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable IndexProfiler to measure each indexing step",
    )
    parser.add_argument(
        "--pytest-args",
        default="",
        help="Extra arguments passed to pytest when running a pytest-benchmark spec",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all benchmarks sequentially",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.all:
        return _run_all(args)

    if not args.spec:
        parser.print_help()
        return 1

    pkg = __package__
    import importlib.util

    bench_dir = os.path.dirname(__file__)
    path = os.path.join(bench_dir, f"{str(args.spec)}.py")
    spec_mod = importlib.util.spec_from_file_location(f"{pkg}.{str(args.spec)}", path)
    if spec_mod is None or spec_mod.loader is None:
        print(f"Could not load spec: {str(args.spec)}", file=sys.stderr)
        return 1
    mod = importlib.util.module_from_spec(spec_mod)
    try:
        spec_mod.loader.exec_module(mod)
    except Exception as e:
        print(f"Failed to load spec {str(args.spec)}: {e}", file=sys.stderr)
        return 1

    # Check if this is a pytest-benchmark style spec (no Spec subclass)
    if not _has_spec_class(mod) and _is_pytest_benchmark_spec(mod):
        extra: list[str] = []
        if args.pytest_args:
            extra = args.pytest_args.split()
        return _run_pytest_spec(
            str(args.spec), extra, report=str(args.report), report_path=str(args.report_path)
        )

    # Otherwise it is a WhooshLikeSpec-based spec
    spec_cls = None
    for attr in dir(mod):
        obj = getattr(mod, attr)
        if isinstance(obj, type) and issubclass(obj, Spec) and obj is not Spec:
            spec_cls = obj
            break
    if spec_cls is None:
        print(f"No Spec subclass found in {str(args.spec)}", file=sys.stderr)
        return 1

    options = argparse.Namespace(
        dir=args.dir,
        limit=args.limit,
        procs=args.procs,
        limitmb=args.limitmb,
        indexname=f"{str(args.spec)}_index",
        progress_every=args.progress_every,
        merge=args.merge,
        chunk=args.chunk,
        skip=args.skip,
        upto=args.upto,
        batch_size=args.batch_size,
        profile=args.profile,
        termfile=None,
    )

    from .reporting import BenchmarkReport, BenchmarkResult

    report = BenchmarkReport(title=f"whoosh-{str(args.spec)}")
    spec = spec_cls(options, [])

    if args.index:
        idx_count, idx_time = _run_indexing(spec, options)
        report.add(
            BenchmarkResult(
                name=str(args.spec),
                category="indexing",
                metric="indexed_docs",
                value=float(idx_count),
                unit="docs",
            )
        )
        if idx_time > 0:
            report.add(
                BenchmarkResult(
                    name=str(args.spec),
                    category="indexing",
                    metric="docs_per_sec",
                    value=idx_count / idx_time,
                    unit="docs/s",
                )
            )

    if args.search:
        search_count, search_time = _run_searching(spec, options)
        report.add(
            BenchmarkResult(
                name=str(args.spec),
                category="querying",
                metric="search_time",
                value=search_time,
                unit="s",
            )
        )
        report.add(
            BenchmarkResult(
                name=str(args.spec),
                category="querying",
                metric="search_results",
                value=float(search_count),
                unit="results",
            )
        )

    if args.ranking:
        search_count, search_time = _run_searching(spec, options)
        print(f"Ranking time: {search_time:.4f}s")
        print(f"Search results: {search_count}")

    if str(args.report) != "none":
        ext = str(args.report)
        out_path = f"{str(args.report_path)}.{ext}"
        if ext == "csv":
            report.to_csv(out_path)
        else:
            report.to_json(out_path)
        print(f"Report written to {out_path}")

    if not args.index and not args.search and not args.ranking:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
