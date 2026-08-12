"""Benchmark analyzer/stemmer performance on stock_etablissements data.

Uses the ``stock_etablissements`` SQLite table from ``benchmark_data.db`` to
measure schema discovery, indexing, and search latency with different
analyzer/stemmer configurations.

Run with::

    python -m benchmark --spec benchmark_stock_etab_analyzer --pytest-args="--benchmark-only"
"""

from __future__ import annotations

import os
import sqlite3
import tempfile

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh import analysis, fields, index, qparser
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.linguistics.stemmers import FrenchAnalyzer

BENCHMARK_DIR = pytest.importorskip("pathlib").Path(__file__).parent
DB_PATH = BENCHMARK_DIR / "benchmark_data.db"


def _get_conn() -> sqlite3.Connection:
    assert DB_PATH.exists(), f"Missing benchmark data: {DB_PATH}"
    return sqlite3.connect(DB_PATH)


class BenchmarkStockEtabAnalyzer:
    """Benchmark suite for analyzer/stemmer on stock_etablissements."""

    def setup_method(self) -> None:
        self._conn = _get_conn()
        self._source = SQLSource(
            connection=self._conn,
            query="SELECT * FROM stock_etablissements",
            incremental_field=None,
            id_field="siret",
        )
        self._schema = self._source.discover_schema()
        self._french_fields = [
            "denominationUsuelleEtablissement",
            "libelleCommuneEtablissement",
            "libellePaysEtrangerEtablissement",
        ]
        self._french_schema = self._source.discover_schema()
        for name in self._french_fields:
            if name in self._french_schema:
                self._french_schema[name].analyzer = FrenchAnalyzer()

    def teardown_method(self) -> None:
        self._conn.close()

    def benchmark_schema_discovery_default(self, benchmark) -> None:
        """Schema discovery with default analyzer (no stemming)."""
        source = SQLSource(
            connection=_get_conn(),
            query="SELECT * FROM stock_etablissements",
            incremental_field=None,
            id_field="siret",
        )
        benchmark(source.discover_schema)

    def benchmark_schema_discovery_french_stemmer(self, benchmark) -> None:
        """Schema discovery with French stemmer on text fields."""
        source = SQLSource(
            connection=_get_conn(),
            query="SELECT * FROM stock_etablissements",
            incremental_field=None,
            id_field="siret",
        )
        schema = source.discover_schema()
        text_fields = [name for name, field in schema.items() if isinstance(field, fields.TEXT)]
        modified = 0
        for name in text_fields:
            if modified < 3:
                schema[name].analyzer = FrenchAnalyzer()
                modified += 1
        benchmark(lambda: schema)

    def benchmark_indexing_default_analyzer(self, benchmark) -> None:
        """Indexing throughput with default analyzer."""
        import tempfile
        from whoosh import index

        source = SQLSource(
            connection=self._conn,
            query="SELECT * FROM stock_etablissements",
            incremental_field=None,
            id_field="siret",
        )
        schema = source.discover_schema()
        docs = list(source.iter_documents())

        with tempfile.TemporaryDirectory() as tmpdir:
            ix = index.create_in(tmpdir, schema)

            def _index() -> None:
                writer = ix.writer()
                for doc in docs:
                    writer.add_document(**doc)
                writer.commit()

            benchmark(_index)

    def benchmark_indexing_french_stemmer(self, benchmark) -> None:
        """Indexing throughput with French stemmer on main text fields."""
        import tempfile
        from whoosh import index

        source = SQLSource(
            connection=self._conn,
            query="SELECT * FROM stock_etablissements",
            incremental_field=None,
            id_field="siret",
        )
        schema = source.discover_schema()
        french_fields = ["denominationUsuelleEtablissement", "libelleCommuneEtablissement", "libellePaysEtrangerEtablissement"]
        for name in french_fields:
            if name in schema:
                schema[name].analyzer = FrenchAnalyzer()
        docs = list(source.iter_documents())

        with tempfile.TemporaryDirectory() as tmpdir:
            ix = index.create_in(tmpdir, schema)

            def _index() -> None:
                writer = ix.writer()
                for doc in docs:
                    writer.add_document(**doc)
                writer.commit()

            benchmark(_index)

    def benchmark_search_default_analyzer(self, benchmark) -> None:
        """Search latency with default analyzer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ix = index.create_in(tmpdir, self._schema)
            writer = ix.writer()
            for doc in self._source.iter_documents():
                writer.add_document(**doc)
            writer.commit()

            searcher = ix.searcher()
            parser = qparser.QueryParser("denominationUsuelleEtablissement", schema=ix.schema)

            def _search() -> None:
                q = parser.parse("SAINT-NAZAIRE")
                searcher.search(q, limit=10)

            benchmark(_search)

    def benchmark_search_french_stemmer(self, benchmark) -> None:
        """Search latency with French stemmer."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ix = index.create_in(tmpdir, self._french_schema)
            writer = ix.writer()
            for doc in self._source.iter_documents():
                writer.add_document(**doc)
            writer.commit()

            searcher = ix.searcher()
            parser = qparser.QueryParser("denominationUsuelleEtablissement", schema=ix.schema)

            def _search() -> None:
                q = parser.parse("SAINT-NAZAIRE")
                searcher.search(q, limit=10)

            benchmark(_search)

    def benchmark_search_french_stemmer(self, benchmark) -> None:
        """Search latency with French stemmer."""
        import tempfile
        from whoosh import index, qparser

        source = SQLSource(
            connection=self._conn,
            query="SELECT * FROM stock_etablissements",
            incremental_field=None,
            id_field="siret",
        )
        schema = source.discover_schema()
        french_fields = ["denominationUsuelleEtablissement", "libelleCommuneEtablissement", "libellePaysEtrangerEtablissement"]
        for name in french_fields:
            if name in schema:
                schema[name].analyzer = FrenchAnalyzer()

        with tempfile.TemporaryDirectory() as tmpdir:
            ix = index.create_in(tmpdir, schema)
            writer = ix.writer()
            for doc in source.iter_documents():
                writer.add_document(**doc)
            writer.commit()

            searcher = ix.searcher()
            parser = qparser.QueryParser("denominationUsuelleEtablissement", schema=ix.schema)

            def _search() -> None:
                q = parser.parse("SAINT-NAZAIRE")
                searcher.search(q, limit=10)

            benchmark(_search)
