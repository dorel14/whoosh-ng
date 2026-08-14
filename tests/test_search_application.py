"""Tests for SearchApplication."""

from __future__ import annotations

from typing import Any

import pytest

from whoosh.fields import TEXT, Schema
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


class TestSearchApplicationEmbedding:
    def test_build_adds_vector_field_from_middleware(self, tmp_path: Any) -> None:
        documents = [{"title": "hello", "content": "world"}]
        source = _FakeDataSource(documents)

        from unittest.mock import MagicMock

        from whoosh_modern.fields import VECTOR
        from whoosh_modern.middleware.embedding import EmbeddingMiddleware
        from whoosh_modern.views.search import SearchView

        provider = MagicMock()
        provider.embed.return_value = [0.1, 0.2, 0.3]

        view = SearchView(
            name="test",
            source=source,
            middleware=[
                EmbeddingMiddleware(
                    embedding_provider=provider,
                    source_field="content",
                    target_field="embedding",
                ),
            ],
        )
        index = view.build(str(tmp_path / "index"))
        assert "embedding" in index.schema
        assert isinstance(index.schema["embedding"], VECTOR)
        assert index.schema["embedding"].stored is True

    def test_build_indexes_embedding_vector(self, tmp_path: Any) -> None:
        documents = [{"title": "hello", "content": "world"}]
        source = _FakeDataSource(documents)

        from unittest.mock import MagicMock

        from whoosh_modern.middleware.embedding import EmbeddingMiddleware
        from whoosh_modern.views.search import SearchView

        provider = MagicMock()
        provider.embed.return_value = [0.1, 0.2, 0.3]

        view = SearchView(
            name="test",
            source=source,
            middleware=[
                EmbeddingMiddleware(
                    embedding_provider=provider,
                    source_field="content",
                    target_field="embedding",
                ),
            ],
        )
        index = view.build(str(tmp_path / "index"))
        with index.searcher() as searcher:
            results = list(searcher.all_stored_fields())
            assert len(results) == 1
            assert results[0]["embedding"] == [0.1, 0.2, 0.3]

    def test_build_supports_multiple_vector_fields(self, tmp_path: Any) -> None:
        documents = [{"title": "hello", "content": "world"}]
        source = _FakeDataSource(documents)

        from unittest.mock import MagicMock

        from whoosh_modern.fields import VECTOR
        from whoosh_modern.middleware.embedding import EmbeddingMiddleware
        from whoosh_modern.views.search import SearchView

        provider = MagicMock()
        provider.embed.side_effect = [[2.0], [5.0]]

        view = SearchView(
            name="test",
            source=source,
            middleware=[
                EmbeddingMiddleware(
                    embedding_provider=provider,
                    embedding_fields=[
                        {"source_field": "title", "target_field": "title_vector"},
                        {"source_field": "content", "target_field": "body_vector"},
                    ],
                ),
            ],
        )
        index = view.build(str(tmp_path / "index"))
        assert "title_vector" in index.schema
        assert "body_vector" in index.schema
        assert isinstance(index.schema["title_vector"], VECTOR)
        assert isinstance(index.schema["body_vector"], VECTOR)
        with index.searcher() as searcher:
            results = list(searcher.all_stored_fields())
            assert len(results) == 1
            assert results[0]["title_vector"] == [2.0]
            assert results[0]["body_vector"] == [5.0]
