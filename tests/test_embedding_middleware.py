"""Middleware integration tests for embeddings.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from whoosh.middleware.context import MiddlewareContext
from whoosh_modern.middleware.embedding import EmbeddingMiddleware


def test_embedding_middleware_no_provider() -> None:
    """Test middleware is a no-op when no provider is configured."""
    middleware = EmbeddingMiddleware(embedding_provider=None)
    context = MiddlewareContext("index")
    context.document = {"content": "hello"}
    result = middleware.before_index(context)
    assert result.document == {"content": "hello"}


def test_embedding_middleware_enriches_document() -> None:
    """Test middleware enriches document with embedding."""
    provider = MagicMock()
    provider.embed.return_value = [0.1, 0.2, 0.3]
    middleware = EmbeddingMiddleware(
        embedding_provider=provider,
        source_field="content",
        target_field="embedding",
    )
    context = MiddlewareContext("index")
    context.document = {"content": "hello world"}
    result = middleware.before_index(context)
    assert result.document is not None
    assert result.document["embedding"] == [0.1, 0.2, 0.3]
    provider.embed.assert_called_once_with("hello world")


def test_embedding_middleware_skips_non_string() -> None:
    """Test middleware skips embedding when field is not a string."""
    provider = MagicMock()
    middleware = EmbeddingMiddleware(
        embedding_provider=provider,
        source_field="content",
        target_field="embedding",
    )
    context = MiddlewareContext("index")
    context.document = {"content": 123}
    result = middleware.before_index(context)
    assert result.document is not None
    assert "embedding" not in result.document
    provider.embed.assert_not_called()


def test_embedding_middleware_handles_error() -> None:
    """Test middleware handles provider errors gracefully."""
    provider = MagicMock()
    provider.embed.side_effect = RuntimeError("boom")
    middleware = EmbeddingMiddleware(
        embedding_provider=provider,
        source_field="content",
        target_field="embedding",
    )
    context = MiddlewareContext("index")
    context.document = {"content": "hello"}
    result = middleware.before_index(context)
    assert result.document == {"content": "hello"}


def test_embedding_middleware_multi_field() -> None:
    """Test middleware enriches multiple fields with embeddings."""
    provider = MagicMock()
    provider.embed.side_effect = lambda text: [float(len(text))]
    middleware = EmbeddingMiddleware(
        embedding_provider=provider,
        embedding_fields=[
            {"source_field": "title", "target_field": "title_vector"},
            {"source_field": "body", "target_field": "body_vector"},
        ],
    )
    context = MiddlewareContext("index")
    context.document = {"title": "Hi", "body": "World"}
    result = middleware.before_index(context)
    assert result.document is not None
    assert result.document["title_vector"] == [2.0]
    assert result.document["body_vector"] == [5.0]
    assert provider.embed.call_count == 2


def test_embedding_middleware_multi_field_skips_missing() -> None:
    """Test middleware skips missing source fields in multi-field mode."""
    provider = MagicMock()
    middleware = EmbeddingMiddleware(
        embedding_provider=provider,
        embedding_fields=[
            {"source_field": "title", "target_field": "title_vector"},
            {"source_field": "body", "target_field": "body_vector"},
        ],
    )
    context = MiddlewareContext("index")
    context.document = {"title": "Hi"}
    result = middleware.before_index(context)
    assert result.document is not None
    assert result.document["title_vector"] is not None
    assert "body_vector" not in result.document
    provider.embed.assert_called_once_with("Hi")
