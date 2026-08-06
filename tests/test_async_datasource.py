"""Tests for async data source methods."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest

from whoosh_modern.data_sources.sql import SQLSource
from whoosh_modern.data_sources.rest import RESTSource


pytestmark = pytest.mark.asyncio


class FakeConnection:
    def __init__(self, rows):
        self._rows = rows
        self._columns = ["id", "name"]

    def cursor(self):
        return FakeCursor(self._rows, self._columns)


class FakeCursor:
    def __init__(self, rows, columns):
        self._rows = rows
        self._columns = columns
        self.description = [(c, None) for c in columns]

    def execute(self, query, params=None):
        pass

    def fetchone(self):
        return (len(self._rows),)

    def fetchmany(self, size):
        return self._rows[:size]

    def __iter__(self):
        return iter(self._rows)


class TestAsyncSQLSource:
    @pytest.fixture
    def sql_source(self):
        rows = [(1, "alpha"), (2, "beta")]
        return SQLSource(connection=FakeConnection(rows), query="SELECT * FROM items")

    async def test_aiter_documents(self, sql_source) -> None:
        docs = []
        async for doc in sql_source.aiter_documents():
            docs.append(doc)
        assert len(docs) == 2
        assert docs[0]["name"] == "alpha"

    async def test_adiscover_schema(self, sql_source) -> None:
        schema = await sql_source.adiscover_schema()
        assert "id" in schema
        assert "name" in schema


class TestAsyncRESTSource:
    @pytest.fixture
    def rest_source(self):
        class _FakeClient:
            def fetch(self, url, headers):
                return {"results": [{"id": 1, "name": "alpha"}]}

        source = RESTSource.__new__(RESTSource)
        source.url = "http://fake.test"
        source.method = "GET"
        source.params = {}
        source.headers = {}
        source.auth = None
        source.pagination = None
        source.page_size = 100
        source.document_path = None
        source.incremental_field = None
        source.timeout = 30
        source._schema = None
        source._http_client = _FakeClient()
        source._total_count = None
        return source

    async def test_aiter_documents(self, rest_source) -> None:
        docs = []
        async for doc in rest_source.aiter_documents():
            docs.append(doc)
        assert len(docs) == 1
        assert docs[0]["name"] == "alpha"
