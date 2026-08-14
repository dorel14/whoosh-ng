"""Tests for FastEmbedProvider.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import sys
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider

pytest.importorskip("fastembed")


@pytest.fixture
def mock_fastembed() -> Generator[MagicMock, None, None]:
    """Provide a mocked FastEmbed TextEmbedding instance."""
    mock_model = MagicMock()
    mock_model.dim = 384
    mock_model.embed.return_value = [
        np.array([0.1, 0.2, 0.3] * 128, dtype=np.float32),
        np.array([0.4, 0.5, 0.6] * 128, dtype=np.float32),
    ]
    with patch("fastembed.TextEmbedding", return_value=mock_model):
        yield mock_model


def test_init_default_model(mock_fastembed: MagicMock) -> None:
    """Test default initialization."""
    provider = FastEmbedProvider()
    assert provider._model_name == "BAAI/bge-small-en-v1.5"
    assert provider.dimension == 384


def test_init_custom_model(mock_fastembed: MagicMock) -> None:
    """Test custom model name."""
    provider = FastEmbedProvider(model_name="BAAI/bge-base-en-v1.5")
    assert provider._model_name == "BAAI/bge-base-en-v1.5"


def test_dimension(mock_fastembed: MagicMock) -> None:
    """Test dimension property."""
    provider = FastEmbedProvider()
    assert provider.dimension == 384


def test_embed_single(mock_fastembed: MagicMock) -> None:
    """Test embedding a single text."""
    provider = FastEmbedProvider()
    vector = provider.embed("hello world")
    assert len(vector) == 384
    assert isinstance(vector[0], float)


def test_embed_batch(mock_fastembed: MagicMock) -> None:
    """Test embedding a batch of texts."""
    provider = FastEmbedProvider()
    vectors = provider.embed_batch(["hello", "world"])
    assert len(vectors) == 2
    assert all(len(v) == 384 for v in vectors)
    assert all(isinstance(v[0], float) for v in vectors)


def test_embed_batch_empty(mock_fastembed: MagicMock) -> None:
    """Test embedding an empty batch."""
    mock_fastembed.embed.return_value = []
    provider = FastEmbedProvider()
    vectors = provider.embed_batch([])
    assert vectors == []


def test_import_error() -> None:
    """Test ImportError when fastembed is not installed."""
    with patch.dict("sys.modules", {"fastembed": None}), pytest.raises(ImportError):
        FastEmbedProvider()
