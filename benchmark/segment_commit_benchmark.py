"""Segment/commit benchmark for Whoosh-NG.

Uses the customers CSV dataset to profile the full commit pipeline:
- merge
- flush
- write_postings / write_terms / write_vectors
- toc_update
- finish

Also measures BufferedPostingWriter vs default writer when applicable.

Usage::

    python -m benchmark.segment_commit_benchmark --upto 5000
    python -m benchmark.segment_commit_benchmark --spec customers_csv --upto 10000
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time

from benchmark import WhooshLikeSpec
from whoosh import fields, index
from whoosh.writing import SegmentWriter
from whoosh_modern.profiling.commit_profiler_v2 import (
    CommitProfilerV2,
    _TimedSegmentWriter,
    profile_commit,
)


class SegmentCommitBenchmark(WhooshLikeSpec):
    name = "segment_commit_benchmark"
    main_field = "City"
    headline_field = "First_Name"
    default_query = "Bradleymouth"

    def __init__(self, options, args):
        super().__init__(options, args)
        csv_path = os.path.join(
            self.options.dir, "Datas", "customers-2000000.csv"
        )
        try:
            from whoosh_modern.data_sources.fast_csv import FastCSVSource

            self._source = FastCSVSource(
                path=csv_path,
                incremental_field=None,
                id_field="Customer Id",
            )
        except ImportError:
            import csv

            class _CSVSource:
                def __init__(self, path):
                    self._path = path

                def discover_schema(self):
                    with open(self._path, newline="", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        row = next(reader, {})
                    return fields.Schema(
                        customer_id=fields.ID(stored=True, unique=True),
                        first_name=fields.TEXT(stored=True),
                        last_name=fields.TEXT(stored=True),
                        company=fields.TEXT(stored=True),
                        city=fields.TEXT(stored=True),
                        country=fields.TEXT(stored=True),
                        email=fields.TEXT(stored=True),
                        subscription_date=fields.TEXT(stored=True),
                        website=fields.TEXT(stored=True),
                    )

                def iter_documents(self):
                    with open(self._path, newline="", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            yield {
                                "customer_id": row["Customer Id"],
                                "first_name": row["First Name"],
                                "last_name": row["Last Name"],
                                "company": row["Company"],
                                "city": row["City"],
                                "country": row["Country"],
                                "email": row["Email"],
                                "subscription_date": row["Subscription Date"],
                                "website": row["Website"],
                            }

            self._source = _CSVSource(csv_path)

    def whoosh_schema(self):
        return self._source.discover_schema()

    def documents(self):
        yield from self._source.iter_documents()

    def batches(self, batch_size: int = 1000):
        yield from self._source.stream_batches(batch_size=batch_size)


def _run(args: argparse.Namespace) -> int:
    upto = int(args.upto) if args.upto else 0
    docs = []
    spec = SegmentCommitBenchmark(
        argparse.Namespace(dir=args.dir, limit=10, merge=1, upto=upto), []
    )
    for i, doc in enumerate(spec.documents()):
        if upto and i >= upto:
            break
        docs.append(doc)

    schema = spec.whoosh_schema()
    idx_dir = os.path.join(args.dir, "indexes", "segment_commit_benchmark_idx")
    if os.path.exists(idx_dir):
        shutil.rmtree(idx_dir)
    os.makedirs(idx_dir, exist_ok=True)

    ix = index.create_in(idx_dir, schema)

    t0 = time.perf_counter()
    writer = ix.writer(limitmb=128, multisegment=not args.single_segment)
    for doc in docs:
        writer.add_document(**doc)
    add_elapsed = time.perf_counter() - t0
    print(f"Added {len(docs)} docs in {add_elapsed:.3f}s")

    profiler = CommitProfilerV2(collect_term_stats=args.term_stats)
    profiler = profile_commit(writer, collect_term_stats=args.term_stats)
    total_elapsed = time.perf_counter() - t0
    print(f"Committed in {total_elapsed:.3f}s")
    print()
    print(profiler.report())
    print(f"Total elapsed (add + commit): {total_elapsed:.3f}s")

    if args.json:
        import json

        out_path = os.path.join(args.dir, "segment_commit_profile.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(profiler.to_dict(), f, indent=2)
        print(f"Profile JSON written to {out_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Whoosh-NG segment/commit benchmark with CommitProfilerV2"
    )
    parser.add_argument(
        "--spec",
        default="segment_commit_benchmark",
        help="Benchmark spec name (default: segment_commit_benchmark)",
    )
    parser.add_argument(
        "--upto",
        default=0,
        help="Max documents to index (0=unlimited)",
    )
    parser.add_argument(
        "--dir",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Benchmark working directory",
    )
    parser.add_argument(
        "--single-segment",
        action="store_true",
        help="Disable multisegment, so merge is skipped and commit is not hidden by segment merge",
    )
    parser.add_argument(
        "--term-stats",
        action="store_true",
        help="Collect term statistics (posting list distribution, blocks per term)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Write profiling results to segment_commit_profile.json",
    )
    return _run(parser.parse_args(list(argv) if argv is not None else None))


if __name__ == "__main__":
    raise SystemExit(main())
