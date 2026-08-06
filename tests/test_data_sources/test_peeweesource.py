"""Tests for PeeweeSource (optional backend)."""

import pytest

peewee = pytest.importorskip("peewee")
from peewee import Model  # noqa: E402

from whoosh_modern.data_sources.peewee_ds import PeeweeSource
from whoosh_modern.exceptions import DataSourceError

# Use an in-memory SQLite database shared by Peewee
DB = peewee.SqliteDatabase(":memory:")


class BaseModel(Model):
    class Meta:
        database = DB


class Article(BaseModel):
    title = peewee.CharField()
    body = peewee.TextField()


def _setup_db():
    if DB.is_closed():
        DB.connect()
    DB.create_tables([Article], safe=True)
    Article.delete().execute()
    Article.create(title="Hello", body="World")
    Article.create(title="Python", body="Tips")
    return DB


class TestPeeweeSource:
    def test_health_check(self):
        _setup_db()
        source = PeeweeSource(model=Article)
        assert source.health_check() is True

    def test_discover_schema(self):
        _setup_db()
        source = PeeweeSource(model=Article)
        schema = source.discover_schema()
        assert "id" in schema
        assert "title" in schema
        assert "body" in schema

    def test_iter_documents(self):
        _setup_db()
        source = PeeweeSource(model=Article)
        docs = list(source.iter_documents())
        assert len(docs) == 2
        assert docs[0]["title"] == "Hello"

    def test_document_count(self):
        _setup_db()
        source = PeeweeSource(model=Article)
        assert source.document_count() == 2

    def test_metadata(self):
        _setup_db()
        source = PeeweeSource(model=Article)
        meta = source.metadata()
        assert meta["type"] == "peewee"
        assert meta["table"] == "article"

    def test_name_property(self):
        _setup_db()
        source = PeeweeSource(model=Article)
        assert source.name == "peewee:article"

    def test_no_model_or_query_raises(self):
        with pytest.raises(DataSourceError):
            PeeweeSource()
