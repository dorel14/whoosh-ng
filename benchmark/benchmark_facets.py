"""Benchmarks for FacetManager performance."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh.fields import BOOLEAN, DATETIME, KEYWORD, NUMERIC, TEXT, Schema
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.facets import FacetManager, RangeFacet, TermsFacet
from whoosh_modern.schema_discovery import SchemaDiscovery

BENCHMARK_DIR = Path(__file__).parent
DB_PATH = str(BENCHMARK_DIR / "benchmark_data.db")


def _discover_schema_from_source(source: SQLSource):
    """Discover schema from a SQLSource."""
    docs = list(source.iter_documents())
    return SchemaDiscovery.from_sample(docs)


class BenchmarkFacetManager:
    """Benchmark suite for FacetManager performance."""

    def setup_method(self):
        self.conn = sqlite3.connect(DB_PATH)
        source = SQLSource(
            connection=self.conn,
            query="SELECT * FROM reuters_articles",
        )
        self.schema = _discover_schema_from_source(source)
        self.facet_manager = FacetManager(self.schema)

    def teardown_method(self):
        self.conn.close()

    def benchmark_auto_discovery(self, benchmark):
        """Benchmark auto-discovery of facetable fields from discovered schema."""

        def _discover():
            return FacetManager(self.schema)

        manager = benchmark(_discover)
        assert manager is not None

    def benchmark_get_facets(self, benchmark):
        """Benchmark getting all facet configs."""

        def _get():
            return self.facet_manager.get_facets()

        facets = benchmark(_get)
        assert isinstance(facets, dict)

    def benchmark_get_facet_config(self, benchmark):
        """Benchmark getting single facet config."""

        def _get():
            return self.facet_manager.get_facet_config("category")

        config = benchmark(_get)
        # Returns None or config dict

    def benchmark_get_all_facet_configs(self, benchmark):
        """Benchmark getting all facet configs."""

        def _get():
            return self.facet_manager.get_all_facet_configs()

        configs = benchmark(_get)
        assert isinstance(configs, dict)

    def benchmark_is_facetable(self, benchmark):
        """Benchmark checking if field is facetable."""

        def _check():
            return self.facet_manager.is_facetable("category")

        result = benchmark(_check)
        assert isinstance(result, bool)

    def benchmark_get_facet_stats(self, benchmark):
        """Benchmark facet statistics generation."""

        def _stats():
            return self.facet_manager.get_facet_stats()

        stats = benchmark(_stats)
        assert "total_fields" in stats

    def benchmark_set_manual_override(self, benchmark):
        """Benchmark setting manual facet overrides."""

        def _override():
            self.facet_manager.set_manual_override(
                "category",
                {"type": "terms", "limit": 50},
            )

        benchmark(_override)

    def benchmark_large_schema(self, benchmark):
        """Benchmark facet manager with large schema from data source."""
        source = SQLSource(
            connection=self.conn,
            query="SELECT * FROM reuters_articles",
        )
        schema = _discover_schema_from_source(source)

        def _create():
            return FacetManager(schema)

        manager = benchmark(_create)
        assert manager is not None


class BenchmarkFacetManagerEdgeCases:
    """Benchmark edge cases for FacetManager."""

    def setup_method(self):
        self.conn = sqlite3.connect(DB_PATH)
        source = SQLSource(
            connection=self.conn,
            query="SELECT * FROM dictionary_entries",
        )
        self.schema = _discover_schema_from_source(source)
        self.facet_manager = FacetManager(self.schema)

    def teardown_method(self):
        self.conn.close()

    def benchmark_empty_schema(self, benchmark):
        """Benchmark facet manager with empty schema."""
        empty_schema = SchemaDiscovery.from_sample([])

        def _create():
            return FacetManager(empty_schema)

        manager = benchmark(_create)
        assert manager is not None

    def benchmark_no_facetable_fields(self, benchmark):
        """Benchmark schema with no facetable fields."""
        from whoosh.fields import NUMERIC

        schema = Schema(
            id=NUMERIC(),
            score=NUMERIC(),
        )

        def _create():
            return FacetManager(schema)

        manager = benchmark(_create)
        assert manager is not None

    def benchmark_mixed_field_types(self, benchmark):
        """Benchmark schema with mixed field types."""
        schema = self.schema

        def _create():
            return FacetManager(schema)

        manager = benchmark(_create)
        assert manager is not None
