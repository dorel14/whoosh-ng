"""Component benchmarks for JSONSource on large gouv_local JSON."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh_modern.data_sources.json import JSONSource

BENCHMARK_DIR = Path(__file__).parent
JSON_PATH = (
    BENCHMARK_DIR / "Datas" / "all_latest" / "2026-07-31_053230-data.gouv_local.json"
)


class BenchmarkJSONSource:
    """Benchmark suite for JSONSource on gouv_local dataset."""

    def setup_method(self):
        self.source = JSONSource(
            path=str(JSON_PATH),
            document_path="service",
            incremental_field=None,
            id_field="id",
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
        assert meta["type"] == "json"
        assert meta["path"] == str(JSON_PATH)
