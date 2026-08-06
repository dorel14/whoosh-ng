"""Tests for PydanticSource."""

from typing import Any

import pytest

pydantic = pytest.importorskip("pydantic")

from whoosh_modern.data_sources.pydantic import PydanticSource
from whoosh_modern.exceptions import DataSourceError


class Article(pydantic.BaseModel):  # type: ignore[name-defined]
    """Test Pydantic model."""

    id: int
    title: str
    body: str


class TestPydanticSource:
    def test_health_check_non_empty(self):
        models = [Article(id=1, title="Hello", body="World")]
        source = PydanticSource(models=models, model=Article)
        assert source.health_check() is True

    def test_empty_models_raises(self):
        with pytest.raises(DataSourceError):
            PydanticSource(models=[])

    def test_discover_schema(self):
        models = [Article(id=1, title="Hello", body="World")]
        source = PydanticSource(models=models, model=Article)
        schema = source.discover_schema()
        assert "id" in schema
        assert "title" in schema
        assert "body" in schema

    def test_iter_documents(self):
        models = [
            Article(id=1, title="Hello", body="World"),
            Article(id=2, title="Python", body="Tips"),
        ]
        source = PydanticSource(models=models, model=Article)
        docs = list(source.iter_documents())
        assert len(docs) == 2
        assert docs[0]["id"] == 1
        assert docs[0]["title"] == "Hello"

    def test_document_count(self):
        models = [
            Article(id=1, title="Hello", body="World"),
            Article(id=2, title="Python", body="Tips"),
        ]
        source = PydanticSource(models=models, model=Article)
        assert source.document_count() == 2

    def test_metadata(self):
        models = [Article(id=1, title="Hello", body="World")]
        source = PydanticSource(
            models=models,
            model=Article,
            incremental_field="id",
            id_field="id",
        )
        meta = source.metadata()
        assert meta["type"] == "pydantic"
        assert meta["model"] == "Article"
        assert meta["count"] == 1

    def test_name_property(self):
        models = [Article(id=1, title="Hello", body="World")]
        source = PydanticSource(models=models, model=Article)
        assert source.name == "pydantic:Article"

    def test_iter_changes_returns_empty(self):
        models = [Article(id=1, title="Hello", body="World")]
        source = PydanticSource(models=models, model=Article)
        docs = list(source.iter_changes(None))
        assert docs == []

    def test_incremental_field_metadata(self):
        models = [Article(id=1, title="Hello", body="World")]
        source = PydanticSource(
            models=models,
            model=Article,
            incremental_field="updated_at",
            id_field="id",
        )
        meta = source.metadata()
        assert meta["incremental_field"] == "updated_at"
        assert meta["id_field"] == "id"
