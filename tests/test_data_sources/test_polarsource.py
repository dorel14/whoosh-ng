"""Tests for PolarsSource (optional backend)."""

import pytest

polars = pytest.importorskip("polars")

from whoosh_modern.data_sources.polars_ds import PolarsSource


class TestPolarsSource:
    def test_health_check_non_empty(self):
        df = polars.DataFrame({"id": [1, 2], "title": ["Hello", "World"]})
        source = PolarsSource(dataframe=df)
        assert source.health_check() is True

    def test_health_check_empty(self):
        df = polars.DataFrame({"id": [], "title": []})
        source = PolarsSource(dataframe=df)
        assert source.health_check() is False

    def test_discover_schema(self):
        df = polars.DataFrame({"id": [1, 2], "title": ["Hello", "World"]})
        source = PolarsSource(dataframe=df)
        schema = source.discover_schema()
        assert "id" in schema
        assert "title" in schema

    def test_iter_documents(self):
        df = polars.DataFrame({"id": [1, 2], "title": ["Hello", "World"]})
        source = PolarsSource(dataframe=df)
        docs = list(source.iter_documents())
        assert len(docs) == 2
        assert docs[0]["id"] == 1
        assert docs[0]["title"] == "Hello"

    def test_document_count(self):
        df = polars.DataFrame({"id": [1, 2], "title": ["Hello", "World"]})
        source = PolarsSource(dataframe=df)
        assert source.document_count() == 2

    def test_metadata(self):
        df = polars.DataFrame({"id": [1], "title": ["Hello"]})
        source = PolarsSource(
            dataframe=df,
            incremental_field="id",
            id_field="id",
        )
        meta = source.metadata()
        assert meta["type"] == "polars"
        assert meta["shape"] == (1, 2)

    def test_name_property(self):
        df = polars.DataFrame({"id": [1]})
        source = PolarsSource(dataframe=df)
        assert source.name == f"polars:{id(df)}"
