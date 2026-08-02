"""Tests for SQLAlchemySource (optional backend)."""

import sqlite3

import pytest

pytest.importorskip("sqlalchemy")
from sqlalchemy import create_engine, text

from whoosh_modern.data_sources.sqlalchemy_ds import SQLAlchemySource


def _setup_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE articles (
                id INTEGER PRIMARY KEY,
                title TEXT,
                body TEXT,
                created_at TEXT
            )
        """))
        conn.execute(text("""
            INSERT INTO articles VALUES (1, 'Hello', 'World', '2024-01-01')
        """))
        conn.execute(text("""
            INSERT INTO articles VALUES (2, 'Python', 'Tips', '2024-01-02')
        """))
        conn.commit()
    return engine


class TestSQLAlchemySource:
    def test_health_check(self):
        engine = _setup_db()
        source = SQLAlchemySource(engine=engine, query="SELECT * FROM articles")
        assert source.health_check() is True

    def test_discover_schema(self):
        engine = _setup_db()
        source = SQLAlchemySource(engine=engine, query="SELECT * FROM articles")
        schema = source.discover_schema()
        assert "id" in schema
        assert "title" in schema
        assert "body" in schema

    def test_iter_documents(self):
        engine = _setup_db()
        source = SQLAlchemySource(engine=engine, query="SELECT * FROM articles")
        docs = list(source.iter_documents())
        assert len(docs) == 2
        assert docs[0]["title"] == "Hello"

    def test_document_count(self):
        engine = _setup_db()
        source = SQLAlchemySource(engine=engine, query="SELECT * FROM articles")
        assert source.document_count() == 2

    def test_metadata(self):
        engine = _setup_db()
        source = SQLAlchemySource(engine=engine, query="SELECT * FROM articles")
        meta = source.metadata()
        assert meta["type"] == "sqlalchemy"
        assert meta["dialect"] == "sqlite"

    def test_name_property(self):
        engine = _setup_db()
        source = SQLAlchemySource(engine=engine, query="SELECT * FROM articles")
        assert source.name == "sqlalchemy:SELECT * FROM articles"
