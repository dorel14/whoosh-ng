"""Benchmarks for SearchView end-to-end pipeline performance using real data.

Pipeline order:
  1. Data source → iterate documents
  2. Schema discovery → discover schema from documents
  3. Index build → build Whoosh index from schema + documents
  4. Facets → create facets from discovered schema
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh.fields import BOOLEAN, NUMERIC, TEXT, Schema
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.facets import FacetManager
from whoosh_modern.schema_discovery import SchemaDiscovery
from whoosh_modern.views import SearchView

BENCHMARK_DIR = Path(__file__).parent
DB_PATH = str(BENCHMARK_DIR / "benchmark_data.db")
INDEX_DIR = BENCHMARK_DIR / "indexes"


def _index_path(name: str) -> str:
    return os.path.join(INDEX_DIR, name)


class BenchmarkSearchViewPipeline:
    """Benchmark suite for SearchView pipeline: data → schema → index → facets."""

    def setup_method(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.source = SQLSource(
            connection=self.conn,
            query="SELECT * FROM reuters_articles",
            incremental_field="article_date",
            id_field="id",
        )

    def teardown_method(self):
        self.conn.close()

    def test_pipeline_step_data(self, benchmark):
        """Benchmark step 1: data source document iteration."""

        def _iterate():
            return list(self.source.iter_documents())

        docs = benchmark(_iterate)
        assert len(docs) > 0

    def test_pipeline_step_schema(self, benchmark):
        """Benchmark step 2: schema discovery from documents."""
        docs = list(self.source.iter_documents())

        def _discover():
            return SchemaDiscovery.from_sample(docs)

        schema = benchmark(_discover)
        assert schema is not None
        assert len(schema) > 0

    def test_pipeline_step_index(self, benchmark):
        """Benchmark step 3: index build from schema + documents."""
        schema = self.source.discover_schema()
        view = SearchView(name="reuters", source=self.source)
        idx_path = _index_path("pipeline_index")
        if os.path.exists(idx_path):
            import shutil

            shutil.rmtree(idx_path)

        def _build():
            return view.build(idx_path)

        result = benchmark(_build)
        assert result is not None
        assert len(result) > 0

    def test_pipeline_step_facets(self, benchmark):
        """Benchmark step 4: facet creation from discovered schema."""
        schema = self.source.discover_schema()

        def _facets():
            return FacetManager(schema)

        manager = benchmark(_facets)
        assert manager is not None
