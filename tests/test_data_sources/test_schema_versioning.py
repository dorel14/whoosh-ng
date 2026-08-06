"""Tests for SearchView schema versioning and evolution."""

import os
import tempfile

import pytest

from whoosh.fields import ID, TEXT
from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.views import SearchView


def _create_test_db():
    """Create an in-memory test database."""
    import sqlite3

    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY,
            title TEXT,
            body TEXT
        )
        """
    )
    cursor.executemany(
        "INSERT INTO articles VALUES (?, ?, ?)",
        [
            (1, "Hello World", "Test content."),
            (2, "Python Tips", "Useful tips."),
        ],
    )
    conn.commit()
    return conn


class TestSchemaVersioning:
    def test_build_stores_schema_version(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        view = SearchView(name="test", source=source, schema_version="2.0")
        tmp = tempfile.mkdtemp()
        try:
            view.build(tmp)
            assert view.schema_version == "2.0"
        finally:
            conn.close()
            for f in os.listdir(tmp):
                os.remove(os.path.join(tmp, f))
            os.rmdir(tmp)

    def test_check_schema_version(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        view = SearchView(name="test", source=source, schema_version="1.0")
        tmp = tempfile.mkdtemp()
        try:
            view.build(tmp)
            assert view.check_schema_version() is True
        finally:
            conn.close()
            for f in os.listdir(tmp):
                os.remove(os.path.join(tmp, f))
            os.rmdir(tmp)


class TestSchemaEvolution:
    def test_evolve_schema_adds_fields(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        view = SearchView(name="test", source=source)
        tmp = tempfile.mkdtemp()
        try:
            view.build(tmp)
            view.evolve_schema({"new_field": TEXT(stored=True)})
        finally:
            conn.close()
            for f in os.listdir(tmp):
                os.remove(os.path.join(tmp, f))
            os.rmdir(tmp)

    def test_evolve_schema_raises_before_build(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        view = SearchView(name="test", source=source)
        with pytest.raises(RuntimeError, match="Index not built yet"):
            view.evolve_schema({"new_field": TEXT(stored=True)})
        conn.close()

    def test_evolve_schema_skips_existing_fields(self):
        conn = _create_test_db()
        source = SQLSource(connection=conn, query="SELECT * FROM articles")
        view = SearchView(name="test", source=source)
        tmp = tempfile.mkdtemp()
        try:
            view.build(tmp)
            view.evolve_schema({"title": TEXT(stored=True)})
        finally:
            conn.close()
            for f in os.listdir(tmp):
                os.remove(os.path.join(tmp, f))
            os.rmdir(tmp)
