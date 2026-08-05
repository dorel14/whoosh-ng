"""Tests for DataSourceConfig."""

import sqlite3

import pytest

from whoosh_modern.data_sources.config import DataSourceConfig
from whoosh_modern.data_sources.fast_csv import FastCSVSource
from whoosh_modern.data_sources.json import JSONSource
from whoosh_modern.data_sources.rest import RESTSource
from whoosh_modern.data_sources.sql import SQLSource

pydantic = pytest.importorskip("pydantic")
from whoosh_modern.data_sources.pydantic import PydanticSource  # noqa: E402


class Article(pydantic.BaseModel):  # type: ignore[name-defined]
    """Test Pydantic model."""

    id: int
    title: str
    body: str


class TestDataSourceConfig:
    def test_create_sql_source(self):
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE articles (id INTEGER, title TEXT)")
        cursor.execute("INSERT INTO articles VALUES (1, 'Hello')")
        conn.commit()

        config = DataSourceConfig(
            type="sql",
            connection=conn,
            query="SELECT * FROM articles",
        )
        source = config.create()
        assert isinstance(source, SQLSource)
        conn.close()

    def test_create_csv_source(self):
        import csv
        import os
        import tempfile

        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "title"])
            writer.writeheader()
            writer.writerow({"id": "1", "title": "Hello"})

        try:
            config = DataSourceConfig(type="csv", path=path)
            source = config.create()
            assert isinstance(source, FastCSVSource)
        finally:
            os.remove(path)

    def test_create_json_source(self):
        import json
        import os
        import tempfile

        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([{"id": 1, "title": "Hello"}], f)

        try:
            config = DataSourceConfig(type="json", path=path)
            source = config.create()
            assert isinstance(source, JSONSource)
        finally:
            os.remove(path)

    def test_create_rest_source(self):
        config = DataSourceConfig(
            type="rest",
            url="http://example.com/api",
            pagination="page",
            page_size=10,
        )
        source = config.create()
        assert isinstance(source, RESTSource)

    def test_create_graphql_source(self):
        config = DataSourceConfig(
            type="graphql",
            url="http://example.com/graphql",
            query="{ articles { id } }",
            document_path="articles",
        )
        source = config.create()
        from whoosh_modern.data_sources.graphql import GraphQLSource

        assert isinstance(source, GraphQLSource)

    def test_create_pydantic_source(self):
        models = [Article(id=1, title="Hello", body="World")]
        config = DataSourceConfig(type="pydantic", models=models, model=Article)
        source = config.create()
        assert isinstance(source, PydanticSource)

    def test_unsupported_type_raises(self):
        config = DataSourceConfig(type="unknown")
        with pytest.raises(ValueError, match="Unsupported DataSource type"):
            config.create()

    def test_sql_missing_connection_raises(self):
        config = DataSourceConfig(type="sql", query="SELECT * FROM x")
        with pytest.raises(ValueError, match="SQLSource requires a 'connection'"):
            config.create()

    def test_sql_missing_query_raises(self):
        conn = sqlite3.connect(":memory:")
        try:
            config = DataSourceConfig(type="sql", connection=conn)
            with pytest.raises(ValueError, match="SQLSource requires a 'query'"):
                config.create()
        finally:
            conn.close()

    def test_csv_missing_path_raises(self):
        config = DataSourceConfig(type="csv")
        with pytest.raises(ValueError, match="CSVSource requires a 'path'"):
            config.create()

    def test_json_missing_path_raises(self):
        config = DataSourceConfig(type="json")
        with pytest.raises(ValueError, match="JSONSource requires a 'path'"):
            config.create()

    def test_graphql_missing_url_raises(self):
        config = DataSourceConfig(type="graphql", query="{ x }")
        with pytest.raises(ValueError, match="GraphQLSource requires a 'url'"):
            config.create()

    def test_graphql_missing_query_raises(self):
        config = DataSourceConfig(type="graphql", url="http://example.com/graphql")
        with pytest.raises(ValueError, match="GraphQLSource requires a 'query'"):
            config.create()

    def test_pydantic_missing_models_raises(self):
        config = DataSourceConfig(type="pydantic")
        with pytest.raises(ValueError, match="PydanticSource requires a 'models'"):
            config.create()
