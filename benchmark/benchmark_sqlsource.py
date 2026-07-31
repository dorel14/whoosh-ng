"""Benchmarks for SQLSource data source indexing performance."""

from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh_modern.data_sources.sql import SQLSource

BENCHMARK_DIR = Path(__file__).parent
DB_PATH = str(BENCHMARK_DIR / "benchmark_data.db")
INDEX_DIR = BENCHMARK_DIR / "indexes"


class BenchmarkSQLSource:
    """Benchmark suite for SQLSource indexing performance using real data."""

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

    def benchmark_discover_schema(self, benchmark):
        """Benchmark schema discovery on real data."""

        def _discover():
            return self.source.discover_schema()

        schema = benchmark(_discover)
        assert schema is not None

    def benchmark_iter_documents(self, benchmark):
        """Benchmark document iteration."""

        def _iterate():
            return list(self.source.iter_documents())

        docs = benchmark(_iterate)
        assert len(docs) > 0

    def benchmark_document_count(self, benchmark):
        """Benchmark document count."""

        def _count():
            return self.source.document_count()

        count = benchmark(_count)
        assert count > 0

    def benchmark_metadata(self, benchmark):
        """Benchmark metadata retrieval."""

        def _meta():
            return self.source.metadata()

        meta = benchmark(_meta)
        assert meta["type"] == "sql"

    def benchmark_iter_changes(self, benchmark):
        """Benchmark incremental changes iteration."""
        since = datetime(1987, 4, 1)

        def _changes():
            return list(self.source.iter_changes(since))

        changes = benchmark(_changes)
        assert isinstance(changes, list)

    def benchmark_group_by_query(self, benchmark):
        """Benchmark GROUP BY aggregation query."""
        conn = sqlite3.connect(DB_PATH)
        source = SQLSource(
            connection=conn,
            query="""
                SELECT article_date, COUNT(*) as doc_count,
                       AVG(word_count) as avg_words
                FROM reuters_articles
                GROUP BY article_date
                ORDER BY article_date DESC
            """,
        )

        def _aggregate():
            return list(source.iter_documents())

        results = benchmark(_aggregate)
        assert len(results) > 0
        conn.close()

    def benchmark_dictionary_source(self, benchmark):
        """Benchmark with dictionary_entries table."""
        conn = sqlite3.connect(DB_PATH)
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM dictionary_entries",
        )

        def _iterate():
            return list(source.iter_documents())

        docs = benchmark(_iterate)
        assert len(docs) > 0
        conn.close()

    def benchmark_indexing_reuters(self, benchmark):
        """Benchmark full indexing of Reuters articles."""
        from whoosh import fields, index
        from whoosh.analysis import StandardAnalyzer

        idx_dir = os.path.join(INDEX_DIR, "sql_reuters_index")
        if os.path.exists(idx_dir):
            shutil.rmtree(idx_dir)
        os.makedirs(idx_dir, exist_ok=True)

        schema = fields.Schema(
            id=fields.ID(stored=True),
            article_date=fields.TEXT(stored=True),
            headline=fields.TEXT(stored=True),
            body=fields.TEXT(analyzer=StandardAnalyzer(), stored=True),
            word_count=fields.NUMERIC(stored=True),
        )

        def _index():
            ix = index.create_in(idx_dir, schema)
            writer = ix.writer()
            count = 0
            for doc in self.source.iter_documents():
                filtered = {
                    k: str(v) if k == "id" else v for k, v in doc.items() if k in schema.names()
                }
                writer.add_document(**filtered)
                count += 1
            writer.commit()
            ix.close()
            return count

        count = benchmark(_index)
        assert count > 0

    def benchmark_indexing_dictionary(self, benchmark):
        """Benchmark full indexing of dictionary entries."""
        from whoosh import fields, index
        from whoosh.analysis import StemmingAnalyzer

        conn = sqlite3.connect(DB_PATH)
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM dictionary_entries",
        )
        idx_dir = os.path.join(INDEX_DIR, "sql_dict_index")
        if os.path.exists(idx_dir):
            shutil.rmtree(idx_dir)
        os.makedirs(idx_dir, exist_ok=True)

        schema = fields.Schema(
            id=fields.ID(stored=True),
            head=fields.TEXT(stored=True),
            body=fields.TEXT(analyzer=StemmingAnalyzer(), stored=True),
            word_count=fields.NUMERIC(stored=True),
        )

        def _index():
            ix = index.create_in(idx_dir, schema)
            writer = ix.writer()
            count = 0
            for doc in source.iter_documents():
                filtered = {
                    k: str(v) if k == "id" else v for k, v in doc.items() if k in schema.names()
                }
                writer.add_document(**filtered)
                count += 1
            writer.commit()
            ix.close()
            return count

        count = benchmark(_index)
        assert count > 0


class BenchmarkSQLSourceEdgeCases:
    """Benchmark edge cases for SQLSource using real data."""

    def setup_method(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.source = SQLSource(
            connection=self.conn,
            query="SELECT * FROM dictionary_entries WHERE id <= 1000",
        )

    def teardown_method(self):
        self.conn.close()

    def benchmark_filtered_query(self, benchmark):
        """Benchmark filtered query with WHERE clause."""

        def _query():
            return list(self.source.iter_documents())

        docs = benchmark(_query)
        assert len(docs) > 0
