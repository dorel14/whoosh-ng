"""Tests for LibEmbeddingProvider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from whoosh_modern.embeddings.libembedding_provider import LibEmbeddingProvider


def test_libembedding_provider_init_defaults() -> None:
    """Test LibEmbeddingProvider initializes with default preset."""
    with patch("libembedding.TextEmbedding") as mock_cls:
        mock_cls.from_mode.return_value.model_name = "BAAI/bge-small-en-v1.5"
        mock_cls.return_value.embed.return_value = np.array([[0.0] * 384])
        provider = LibEmbeddingProvider()
        assert provider.model_name == "BAAI/bge-small-en-v1.5"
        assert provider.dimension == 384


def test_libembedding_provider_init_with_preset() -> None:
    """Test LibEmbeddingProvider resolves 'fast' preset via from_mode."""
    with patch("libembedding.TextEmbedding") as mock_cls:
        mock_cls.from_mode.return_value.model_name = "fast-model"
        mock_cls.return_value.embed.return_value = np.array([[0.0] * 384])
        provider = LibEmbeddingProvider(model_name="fast")
        assert provider.model_name == "fast-model"
        mock_cls.from_mode.assert_called_once_with(mode="fast")


def test_libembedding_provider_init_with_model_name() -> None:
    """Test LibEmbeddingProvider uses model name directly when not a preset."""
    with patch("libembedding.TextEmbedding") as mock_cls:
        mock_cls.return_value.embed.return_value = np.array([[0.0] * 256])
        provider = LibEmbeddingProvider(model_name="custom/model")
        assert provider.model_name == "custom/model"
        mock_cls.assert_called_once_with(model_name="custom/model", pooling="mean")


def test_libembedding_provider_embed() -> None:
    """Test embed returns a list of floats with the correct dimension."""
    with patch("libembedding.TextEmbedding") as mock_cls:
        mock_model = MagicMock()
        mock_model.embed.return_value = np.array([[0.1, 0.2, 0.3, 0.4]])
        mock_cls.return_value = mock_model
        provider = LibEmbeddingProvider.__new__(LibEmbeddingProvider)
        provider._model = mock_model
        provider._model_name = "test-model"
        provider._dimension = 4
        vector = provider.embed("hello world")
        assert isinstance(vector, list)
        assert len(vector) == 4
        assert all(isinstance(v, float) for v in vector)


def test_libembedding_provider_embed_batch() -> None:
    """Test embed_batch returns one vector per input text."""
    with patch("libembedding.TextEmbedding") as mock_cls:
        mock_model = MagicMock()
        mock_model.embed.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_cls.return_value = mock_model
        provider = LibEmbeddingProvider.__new__(LibEmbeddingProvider)
        provider._model = mock_model
        provider._model_name = "test-model"
        provider._dimension = 2
        vectors = provider.embed_batch(["hello", "world"])
        assert len(vectors) == 2
        assert all(len(v) == 2 for v in vectors)
        assert all(isinstance(x, float) for v in vectors for x in v)


def test_libembedding_provider_embed_batch_empty() -> None:
    """Test embed_batch with empty input returns an empty list."""
    with patch("libembedding.TextEmbedding") as mock_cls:
        mock_cls.return_value = MagicMock()
        provider = LibEmbeddingProvider.__new__(LibEmbeddingProvider)
        provider._model = mock_cls.return_value
        provider._model_name = "test-model"
        provider._dimension = 4
        assert provider.embed_batch([]) == []


def test_libembedding_provider_repr() -> None:
    """Test the string representation of the provider."""
    with patch("libembedding.TextEmbedding") as mock_cls:
        mock_cls.return_value.embed.return_value = np.array([[0.0] * 384])
        provider = LibEmbeddingProvider(model_name="balanced")
        r = repr(provider)
        assert "LibEmbeddingProvider" in r
        assert "dimension=384" in r


def test_libembedding_provider_invalid_preset() -> None:
    """Test that an invalid preset raises ValueError from _load_from_mode."""
    with pytest.raises(ValueError, match="Unsupported libembedding preset"):
        LibEmbeddingProvider._load_from_mode("invalid-preset")


def test_libembedding_provider_missing_libembedding() -> None:
    """Test that ImportError is raised when libembedding is not installed."""
    with (
        patch.dict("sys.modules", {"libembedding": None}),
        pytest.raises(ImportError, match="requires libembedding"),
    ):
        LibEmbeddingProvider(model_name="balanced")
