"""Config integration tests for the embedding subsystem.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from whoosh_modern.config.engine import ConfigEngine
from whoosh_modern.config.engines.embedding import EmbeddingEngine
from whoosh_modern.config.models import EmbeddingConfig, WhooshNGConfig


def test_embedding_engine_fastembed() -> None:
    """Test EmbeddingEngine builds a FastEmbedProvider from config."""
    config = WhooshNGConfig(
        embedding=EmbeddingConfig(provider="fastembed", model="BAAI/bge-small-en-v1.5")
    )
    with patch("whoosh_modern.embeddings.fastembed_provider.FastEmbedProvider") as mock:
        mock.return_value = MagicMock()
        result = EmbeddingEngine(config).build()
        assert result is not None
        mock.assert_called_once_with(model_name="BAAI/bge-small-en-v1.5")


def test_embedding_engine_onnx() -> None:
    """Test EmbeddingEngine builds an ONNXEmbeddingProvider from config."""
    config = WhooshNGConfig(
        embedding=EmbeddingConfig(
            provider="onnx",
            model="multilingual-e5-small",
            model_path="models/multilingual-e5-small/model.onnx",
            tokenizer_dir="models/multilingual-e5-small",
            quantization="fp32",
            batch_size=32,
        )
    )
    with patch("whoosh_modern.embeddings.onnx_provider.ONNXEmbeddingProvider") as mock:
        mock.return_value = MagicMock()
        result = EmbeddingEngine(config).build()
        assert result is not None
        mock.assert_called_once_with(
            model_path="models/multilingual-e5-small/model.onnx",
            tokenizer_dir="models/multilingual-e5-small",
            pooling="mean",
            normalize=True,
            dimension=None,
            enable_prefix=True,
            quantization="fp32",
        )


def test_embedding_engine_sentence_transformers() -> None:
    """Test EmbeddingEngine builds a SentenceTransformersProvider from config."""
    config = WhooshNGConfig(
        embedding=EmbeddingConfig(provider="sentence-transformers", model="all-MiniLM-L6-v2")
    )
    with patch(
        "whoosh_modern.embeddings.sentence_transformers_provider.SentenceTransformersProvider"
    ) as mock:
        mock.return_value = MagicMock()
        result = EmbeddingEngine(config).build()
        assert result is not None
        mock.assert_called_once_with(model_name="all-MiniLM-L6-v2")


def test_embedding_engine_unsupported() -> None:
    """Test EmbeddingEngine raises for unsupported provider."""
    config = WhooshNGConfig(embedding=EmbeddingConfig(provider="unknown"))
    with pytest.raises(ValueError, match="Unsupported embedding provider"):
        EmbeddingEngine(config).build()


def test_config_engine_build_uses_embedding_engine() -> None:
    """Test ConfigEngine.build() invokes EmbeddingEngine."""
    engine = ConfigEngine()
    with (
        patch("whoosh_modern.config.engine.EmbeddingEngine") as mock_embedding,
        patch("whoosh_modern.config.engine.DataSourceEngine") as mock_source,
        patch("whoosh_modern.config.engine.StorageEngine") as mock_storage,
        patch("whoosh_modern.config.engine.VectorEngine") as mock_vector,
        patch("whoosh_modern.config.engine.LanguageEngine") as mock_lang,
        patch("whoosh_modern.application.SearchApplication") as mock_app,
    ):
        mock_source.return_value.build.return_value = MagicMock()
        mock_storage.return_value.build.return_value = MagicMock()
        mock_vector.return_value.build.return_value = None
        mock_embedding.return_value.build.return_value = None
        mock_lang.return_value.build.return_value = None
        engine._config = WhooshNGConfig()
        engine.build()
        mock_embedding.assert_called_once()
