"""Benchmarks for schema discovery performance using real data."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.schema_discovery import SchemaDiscovery

BENCHMARK_DIR = Path(__file__).parent
DB_PATH = str(BENCHMARK_DIR / "benchmark_data.db")


class BenchmarkSchemaDiscovery:
    """Benchmark suite for schema discovery performance."""

    def setup_method(self):
        self.conn = sqlite3.connect(DB_PATH)

    def teardown_method(self):
        self.conn.close()

    def test_from_result_set_reuters(self, benchmark):
        """Benchmark schema discovery from Reuters columns using real data source."""
        source = SQLSource(
            connection=self.conn,
            query="SELECT * FROM reuters_articles LIMIT 1",
        )
        docs = list(source.iter_documents())
        columns = [(k, type(v).__name__) for k, v in docs[0].items()] if docs else []

        def _discover():
            return SchemaDiscovery.from_result_set(columns)

        schema = benchmark(_discover)
        assert schema is not None
        assert len(schema) > 0

    def test_from_result_set_dictionary(self, benchmark):
        """Benchmark schema discovery from dictionary columns using real data source."""
        source = SQLSource(
            connection=self.conn,
            query="SELECT * FROM dictionary_entries LIMIT 1",
        )
        docs = list(source.iter_documents())
        columns = [(k, type(v).__name__) for k, v in docs[0].items()] if docs else []

        def _discover():
            return SchemaDiscovery.from_result_set(columns)

        schema = benchmark(_discover)
        assert schema is not None
        assert len(schema) > 0

    def test_from_sample_reuters(self, benchmark):
        """Benchmark schema discovery from Reuters sample documents."""
        source = SQLSource(
            connection=self.conn,
            query="SELECT * FROM reuters_articles LIMIT 10",
        )

        def _discover():
            docs = list(source.iter_documents())
            return SchemaDiscovery.from_sample(docs)

        schema = benchmark(_discover)
        assert schema is not None
        assert len(schema) > 0

    def test_from_sample_dictionary(self, benchmark):
        """Benchmark schema discovery from dictionary sample."""
        source = SQLSource(
            connection=self.conn,
            query="SELECT * FROM dictionary_entries LIMIT 10",
        )

        def _discover():
            docs = list(source.iter_documents())
            return SchemaDiscovery.from_sample(docs)

        schema = benchmark(_discover)
        assert schema is not None
        assert len(schema) > 0

    def test_detect_id_field(self, benchmark):
        """Benchmark ID field detection from discovered schema."""
        source = SQLSource(
            connection=self.conn,
            query="SELECT * FROM reuters_articles",
        )
        schema = source.discover_schema()

        def _detect():
            return SchemaDiscovery.detect_id_field(dict(schema))

        field_name = benchmark(_detect)
        assert field_name == "id"

    def test_from_result_set_with_duplicates(self, benchmark):
        """Benchmark duplicate column detection."""
        source = SQLSource(
            connection=self.conn,
            query="SELECT * FROM reuters_articles LIMIT 1",
        )
        docs = list(source.iter_documents())
        columns = [(k, type(v).__name__) for k, v in docs[0].items()] if docs else []
        columns.append(("id", "INTEGER"))  # Duplicate

        def _discover():
            try:
                return SchemaDiscovery.from_result_set(columns)
            except Exception:
                return None

        result = benchmark(_discover)
        # Should raise for duplicates
