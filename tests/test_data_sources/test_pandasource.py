"""Tests for PandasSource (optional backend)."""

import pytest

pandas = pytest.importorskip("pandas")

from whoosh_modern.data_sources.pandas_ds import PandasSource


class TestPandasSource:
    def test_health_check_non_empty(self):
        df = pandas.DataFrame({"id": [1, 2], "title": ["Hello", "World"]})
        source = PandasSource(dataframe=df)
        assert source.health_check() is True

    def test_health_check_empty(self):
        df = pandas.DataFrame({"id": [], "title": []})
        source = PandasSource(dataframe=df)
        assert source.health_check() is False

    def test_discover_schema(self):
        df = pandas.DataFrame({"id": [1, 2], "title": ["Hello", "World"]})
        source = PandasSource(dataframe=df)
        schema = source.discover_schema()
        assert "id" in schema
        assert "title" in schema

    def test_iter_documents(self):
        df = pandas.DataFrame({"id": [1, 2], "title": ["Hello", "World"]})
        source = PandasSource(dataframe=df)
        docs = list(source.iter_documents())
        assert len(docs) == 2
        assert docs[0]["id"] == 1
        assert docs[0]["title"] == "Hello"

    def test_document_count(self):
        df = pandas.DataFrame({"id": [1, 2], "title": ["Hello", "World"]})
        source = PandasSource(dataframe=df)
        assert source.document_count() == 2

    def test_metadata(self):
        df = pandas.DataFrame({"id": [1], "title": ["Hello"]})
        source = PandasSource(
            dataframe=df,
            incremental_field="id",
            id_field="id",
        )
        meta = source.metadata()
        assert meta["type"] == "pandas"
        assert meta["shape"] == (1, 2)

    def test_name_property(self):
        df = pandas.DataFrame({"id": [1]})
        source = PandasSource(dataframe=df)
        assert source.name == f"pandas:{id(df)}"
