"""Component benchmarks for CSVSource on large customer data."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh_modern.data_sources.fast_csv import FastCSVSource

BENCHMARK_DIR = Path(__file__).parent
CSV_PATH = BENCHMARK_DIR / "Datas" / "customers-2000000.csv"


class BenchmarkCSVSource:
    """Benchmark suite for CSVSource on 2M customer records."""

    def setup_method(self):
        self.source = FastCSVSource(
            path=str(CSV_PATH),
            incremental_field=None,
            id_field="Customer Id",
        )

    def benchmark_discover_schema(self, benchmark):
        schema = benchmark(self.source.discover_schema)
        assert schema is not None
        assert "City" in schema

    def benchmark_iter_documents(self, benchmark):
        docs = benchmark(lambda: list(self.source.iter_documents()))
        assert len(docs) > 0

    def benchmark_document_count(self, benchmark):
        count = benchmark(self.source.document_count)
        assert count > 0

    def benchmark_metadata(self, benchmark):
        meta = benchmark(self.source.metadata)
        assert meta["type"] == "fast_csv"
        assert meta["path"] == str(CSV_PATH)
