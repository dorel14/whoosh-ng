"""Tests for SearchApplication."""

from __future__ import annotations

from typing import Any

import pytest

from whoosh.fields import Schema, TEXT

from whoosh_modern import SearchApplication
from whoosh_modern.data_sources.fast_csv import FastCSVSource
from whoosh_modern.storage import FileStorage


class _FakeDataSource:
    def __init__(self, documents: list[dict[str, Any]]) -> None:
        self._documents = documents
        self._schema = Schema(title=TEXT(stored=True), content=TEXT)

    @property
    def name(self) -> str:
        return "fake"

    def discover_schema(self) -> Schema:
        return self._schema

    def iter_documents(self) -> Any:
        return iter(self._documents)

    def stream_batches(self, batch_size: int = 1000) -> Any:
        yield self._documents

    def health_check(self) -> bool:
        return True


class TestSearchApplication:
    def test_build_creates_index(self, tmp_path: Any) -> None:
        documents = [{"title": "hello", "content": "world"}]
        source = _FakeDataSource(documents)
        storage = FileStorage(str(tmp_path))

        app = SearchApplication(source=source, storage=storage)
        app.build()

        assert app.index is not None
        assert app.index.doc_count() == 1

    def test_search_returns_results(self, tmp_path: Any) -> None:
        documents = [{"title": "hello", "content": "world"}]
        source = _FakeDataSource(documents)
        storage = FileStorage(str(tmp_path))

        app = SearchApplication(source=source, storage=storage)
        app.build()

        results = app.search("title:hello")
        assert len(results) == 1

    def test_build_without_source_raises(self) -> None:
        app = SearchApplication()
        with pytest.raises(ValueError, match="A source is required"):
            app.build()

    def test_index_before_build_raises(self) -> None:
        app = SearchApplication()
        with pytest.raises(RuntimeError, match="Call build"):
            _ = app.index
