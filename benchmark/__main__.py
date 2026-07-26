# Benchmark CLI entry point for Whoosh-NG
# Usage:
#   python -m benchmark --help
#   python -m benchmark --spec reuters --index --search --report csv
#   python -m benchmark --spec dictionary --index --report json

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from whoosh.support.bench import Bench, Spec


def _available_specs() -> list[str]:
    # Lazy import of benchmark specs to avoid heavy imports at startup.
    specs: list[str] = []
    pkg = __package__
    import importlib.util
    import os

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
                spec.loader.exec_module(mod)  # type: ignore[union-attr]
            except Exception:
                continue
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if isinstance(obj, type) and issubclass(obj, Spec) and obj is not Spec:
                    specs.append(name)
                    break
    return sorted(specs)


def main(argv: Sequence[str] | None = None) -> int:
    available = _available_specs()
    parser = argparse.ArgumentParser(
        prog="python -m benchmark", description="Whoosh-NG benchmark runner"
    )
    parser.add_argument(
        "--spec",
        choices=available,
        required=True,
        help="Benchmark spec to run (e.g. reuters, dictionary, enron, marc21)",
    )
    parser.add_argument("--index", action="store_true", help="Run indexing benchmark")
    parser.add_argument("--search", action="store_true", help="Run querying benchmark")
    parser.add_argument("--ranking", action="store_true", help="Run ranking benchmark")
    parser.add_argument("--dir", default=".", help="Working directory for index/data")
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
    parser.add_argument("--every", default=None, help="Report progress every N docs")
    parser.add_argument("--merge", default=1, help="Merge policy (1=SMALL, 0=none)")
    parser.add_argument("--chunk", default=0, help="Chunk size for indexing progress")
    parser.add_argument("--skip", default="1", help="Initial docs to skip (default: 1)")
    parser.add_argument("--upto", default=0, help="Maximum docs to index (0=unlimited)")

    args = parser.parse_args(list(argv) if argv is not None else None)

    pkg = __package__
    import importlib.util
    import os

    bench_dir = os.path.dirname(__file__)
    path = os.path.join(bench_dir, f"{args.spec}.py")
    spec = importlib.util.spec_from_file_location(f"{pkg}.{args.spec}", path)
    if spec is None or spec.loader is None:
        print(f"Could not load spec: {args.spec}", file=sys.stderr)
        return 1
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    spec_cls = None
    for attr in dir(mod):
        obj = getattr(mod, attr)
        if isinstance(obj, type) and issubclass(obj, Spec) and obj is not Spec:
            spec_cls = obj
            break
    if spec_cls is None:
        print(f"No Spec subclass found in {args.spec}", file=sys.stderr)
        return 1

    bench = Bench()
    # add flavor name / git version to the namespace so marvin/spec wiring stays compatible
    bench.options = argparse.Namespace(
        dir=args.dir,
        limit=args.limit,
        procs=args.procs,
        limitmb=args.limitmb,
        indexname=f"{args.spec}_index",
        every=args.every,
        merge=args.merge,
        chunk=args.chunk,
        skip=args.skip,
        upto=args.upto,
        termfile=None,
    )

    from benchmark.reporting import BenchmarkReport, BenchmarkResult

    report = BenchmarkReport(title=f"whoosh-{args.spec}")
    spec = spec_cls(bench.options, [])

    if args.index:
        bench.index(spec)
        idx_count = float(bench._last_index_count)
        idx_time = bench._last_index_time
        report.add(
            BenchmarkResult(
                name=args.spec,
                category="indexing",
                metric="indexed_docs",
                value=idx_count,
                unit="docs",
            )
        )
        if idx_time > 0:
            report.add(
                BenchmarkResult(
                    name=args.spec,
                    category="indexing",
                    metric="docs_per_sec",
                    value=idx_count / idx_time,
                    unit="docs/s",
                )
            )

    if args.search:
        bench.search(spec)
        report.add(
            BenchmarkResult(
                name=args.spec,
                category="querying",
                metric="search_time",
                value=bench._last_search_time,
                unit="s",
            )
        )

    if args.ranking:
        bench.rank(spec)

    if args.report != "none":
        ext = args.report
        out_path = f"{args.report_path}.{ext}"
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
