"""Component benchmarks for ParquetSource on large stock parquet."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh_modern.data_sources.parquet_ds import ParquetSource

BENCHMARK_DIR = Path(__file__).parent
PARQUET_PATH = BENCHMARK_DIR / "Datas" / "stock-stockunitelegale-parquet.parquet"


class BenchmarkParquetSource:
    """Benchmark suite for ParquetSource on 705MB stock dataset."""

    def setup_method(self):
        self.source = ParquetSource(
            path=str(PARQUET_PATH),
            incremental_field=None,
            id_field="siren",
        )

    def benchmark_discover_schema(self, benchmark):
        schema = benchmark(self.source.discover_schema)
        assert schema is not None

    def benchmark_iter_documents(self, benchmark):
        docs = benchmark(lambda: list(self.source.iter_documents()))
        assert len(docs) > 0

    def benchmark_document_count(self, benchmark):
        count = benchmark(self.source.document_count)
        assert count > 0

    def benchmark_metadata(self, benchmark):
        meta = benchmark(self.source.metadata)
        assert meta["type"] == "parquet"
        assert meta["path"] == str(PARQUET_PATH)
