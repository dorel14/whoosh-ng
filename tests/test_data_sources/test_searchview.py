"""Tests for SearchView."""

import os
import sqlite3
import tempfile
from datetime import datetime

import pytest

from whoosh.fields import ID, TEXT, Schema
from whoosh.index import exists_in, open_dir
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.exceptions import ValidationError
from whoosh_modern.middleware import LoggingMiddleware, RetryMiddleware
from whoosh_modern.views import SearchView


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
            created_at TEXT
        )
        """
    )
    cursor.executemany(
        "INSERT INTO articles VALUES (?, ?, ?, ?, ?)",
        [
            (1, "Hello", "Content A", "tech", "2024-01-01"),
            (2, "World", "Content B", "science", "2024-01-15"),
            (3, "Python", "Content C", "tech", "2024-02-01"),
        ],
    )
    conn.commit()
    return conn


class TestSearchView:
    def test_build_index(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            id_field="id",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            view = SearchView(
                name="test_view",
                source=source,
            )
            index = view.build(tmpdir)
            assert index is not None
            assert exists_in(tmpdir)
        conn.close()

    def test_build_with_field_overrides(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            id_field="id",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            view = SearchView(
                name="test_view",
                source=source,
                fields={"title": ID(stored=True)},
            )
            index = view.build(tmpdir)
            schema = index.schema
            assert isinstance(schema["title"], ID)
        conn.close()

    def test_refresh(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            incremental_field="created_at",
            id_field="id",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            view = SearchView(
                name="test_view",
                source=source,
                incremental_field="created_at",
            )
            view.build(tmpdir)
            count = view.refresh()
            assert isinstance(count, int)
        conn.close()

    def test_reindex(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            id_field="id",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            view = SearchView(
                name="test_view",
                source=source,
            )
            view.build(tmpdir)
            count = view.reindex()
            assert count > 0
        conn.close()

    def test_reindex_no_build_raises(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
        )
        view = SearchView(
            name="test_view",
            source=source,
        )
        with pytest.raises(RuntimeError):
            view.reindex()
        conn.close()

    def test_refresh_no_index_raises(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
        )
        view = SearchView(name="test_view", source=source)
        with pytest.raises(RuntimeError):
            view.refresh()
        conn.close()

    def test_search_with_middleware(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            id_field="id",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            view = SearchView(
                name="test_view",
                source=source,
                middleware=[RetryMiddleware(attempts=2)],
            )
            index = view.build(tmpdir)
            assert index is not None
        conn.close()

    def test_search_with_logging_middleware(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            id_field="id",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            view = SearchView(
                name="test_view",
                source=source,
                middleware=[LoggingMiddleware()],
            )
            index = view.build(tmpdir)
            assert index is not None
        conn.close()

    def test_validate(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
            id_field="id",
        )
        view = SearchView(name="test_view", source=source)
        results = view.validate()
        assert len(results) == 4
        conn.close()

    def test_search_without_incremental_returns_zero_on_refresh(self):
        conn = _create_test_db()
        source = SQLSource(
            connection=conn,
            query="SELECT * FROM articles",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            view = SearchView(name="test_view", source=source)
            view.build(tmpdir)
            count = view.refresh()
            assert count == 0
        conn.close()

    def test_prepare_doc_preserves_list_values(self):
        source = SQLSource(
            connection=_create_test_db(),
            query="SELECT * FROM articles",
        )
        view = SearchView(name="test", source=source)
        schema = Schema(
            title=TEXT(stored=True),
            category=TEXT(stored=True),
        )
        doc = {
            "title": "Test",
            "category": "tag1 tag2",
        }
        prepared = view._prepare_doc(doc, schema)
        assert prepared["title"] == "Test"
        assert prepared["category"] == "tag1 tag2"
