"""Tests for async search and writer bridges on Index."""

from __future__ import annotations

import asyncio

import pytest

from whoosh.fields import Schema, TEXT
from whoosh.index import create_in
from whoosh.writing import IndexWriter


pytestmark = pytest.mark.asyncio


@pytest.fixture
def tmp_path_index(tmp_path):
    schema = Schema(title=TEXT(stored=True), content=TEXT)
    return create_in(str(tmp_path), schema)


class TestAsyncSearch:
    async def test_asearch_returns_results(self, tmp_path_index) -> None:
        writer = tmp_path_index.writer()
        writer.add_document(title="hello", content="world")
        writer.commit()

        results = await tmp_path_index.asearch("title:hello")
        assert len(results) == 1

    async def test_asearch_equivalence(self, tmp_path_index) -> None:
        writer = tmp_path_index.writer()
        writer.add_document(title="alpha", content="first")
        writer.add_document(title="beta", content="second")
        writer.commit()

        from whoosh.qparser import QueryParser

        qp = QueryParser("title", schema=tmp_path_index.schema)
        sync_results = tmp_path_index.searcher().search(qp.parse("alpha"))
        async_results = await tmp_path_index.asearch("title:alpha")
        assert len(async_results) == len(sync_results)


class TestAsyncWriter:
    async def test_awriter_context_manager(self, tmp_path_index) -> None:
        async with await tmp_path_index.awriter() as writer:
            assert isinstance(writer, IndexWriter)
            writer.add_document(title="async", content="writer test")

        with tmp_path_index.searcher() as searcher:
            from whoosh.qparser import QueryParser

            qp = QueryParser("title", schema=searcher.schema)
            results = searcher.search(qp.parse("async"))
            assert len(results) == 1

    async def test_awriter_multiple_adds(self, tmp_path_index) -> None:
        async with await tmp_path_index.awriter() as writer:
            writer.add_document(title="doc1", content="content1")
            writer.add_document(title="doc2", content="content2")

        with tmp_path_index.searcher() as searcher:
            assert searcher.doc_count() == 2
