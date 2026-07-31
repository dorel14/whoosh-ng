"""Tests for SQLSource (SQL data source)."""

import sqlite3
from datetime import datetime

import pytest

from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.exceptions import DataSourceError, SchemaDiscoveryError


def _create_test_db():
    """Create an in-memory test database."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY,
            title TEXT,
            body TEXT,
            category TEXT,
            weight REAL,
            is_published BOOLEAN,
            created_at TEXT
        )
        """
    )
    cursor.executemany(
        "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (1, "Hello World", "Test content.", "tech", 1.5, 1, "2024-01-01"),
            (2, "Python Tips", "Useful tips.", "tech", 2.0, 1, "2024-01-15"),
            (3, "Search", "About search.", "science", 3.5, 0, "2024-02-01"),
        ],
    )
    conn.commit()
    return conn


class TestSQLSource:
    def test_discover_schema(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        schema = source.discover_schema()
        assert "id" in schema
        assert "title" in schema
        assert "body" in schema
        assert "category" in schema
        assert "weight" in schema
        assert "is_published" in schema
        assert "created_at" in schema
        conn.close()

    def test_iter_documents(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        docs = list(source.iter_documents())
        assert len(docs) == 3
        assert docs[0]["id"] == 1
        assert docs[0]["title"] == "Hello World"
        conn.close()

    def test_iter_documents_with_where(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="SELECT * FROM articles WHERE category = 'tech'")
        docs = list(source.iter_documents())
        assert len(docs) == 2
        conn.close()

    def test_iter_documents_join(self):
        conn = _create_test_db()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE categories (name TEXT, description TEXT)")
        cursor.execute("INSERT INTO categories VALUES ('tech', 'Technology')")
        conn.commit()
        source = SQLSource(
            connection=conn,
            query="""
            SELECT a.id, a.title, c.description
            FROM articles a
            JOIN categories c ON a.category = c.name
            """,
        )
        docs = list(source.iter_documents())
        assert len(docs) == 2
        conn.close()

    def test_document_count(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        count = source.document_count()
        assert count == 3
        conn.close()

    def test_metadata(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            incremental_field="created_at",
            id_field="id",
        )
        meta = source.metadata()
        assert meta["type"] == "sql"
        assert meta["incremental_field"] == "created_at"
        assert meta["id_field"] == "id"
        conn.close()

    def test_incremental_field_validated(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            incremental_field="nonexistent_field",
        )
        with pytest.raises(DataSourceError):
            source.discover_schema()
        conn.close()

    def test_iter_changes(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            incremental_field="created_at",
        )
        docs = list(source.iter_changes(datetime(2024, 1, 1)))
        assert len(docs) >= 0
        conn.close()

    def test_iter_changes_no_incremental_field(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        docs = list(source.iter_changes(datetime(2024, 1, 1)))
        assert docs == []
        conn.close()

    def test_null_values_handled(self):
        conn = _create_test_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)",
            (4, None, None, None, None, None, None),
        )
        conn.commit()
        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        docs = list(source.iter_documents())
        null_doc = [d for d in docs if d["id"] == 4][0]
        assert null_doc["title"] is None
        conn.close()

    def test_name_property(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        assert source.name.startswith("sql:")
        conn.close()

    def test_invalid_query_raises(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="INVALID SQL STATEMENT")
        with pytest.raises(sqlite3.OperationalError, match="syntax error"):
            source.discover_schema()
        conn.close()

    def test_group_by_query(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="""
            SELECT category, COUNT(*) as doc_count,
                   AVG(weight) as avg_weight
            FROM articles
            GROUP BY category
            """,
        )
        schema = source.discover_schema()
        assert "category" in schema
        assert "doc_count" in schema
        assert "avg_weight" in schema
        docs = list(source.iter_documents())
        assert len(docs) > 0
        conn.close()

    def test_duplicate_column_names_raise(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT id, id FROM articles",
        )
        with pytest.raises(SchemaDiscoveryError):
            source.discover_schema()
        conn.close()

    def test_document_count_non_select_raises(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="DROP TABLE articles")
        with pytest.raises(DataSourceError):
            source.document_count()
        conn.close()

    def test_id_field_metadata(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            id_field="id",
        )
        assert source.id_field == "id"
        conn.close()
