"""Tests for embedding providers."""

from __future__ import annotations

import pytest

from whoosh_modern.embeddings.protocol import EmbeddingProvider
from whoosh_modern.embeddings.sentence_transformers_provider import (
    SentenceTransformersProvider,
)


def test_sentence_transformers_provider_embed() -> None:
    pytest.importorskip("sentence_transformers", reason="sentence-transformers not installed")
    provider = SentenceTransformersProvider()
    vector = provider.embed("hello world")
    assert len(vector) > 0
    assert all(isinstance(v, float) for v in vector)
