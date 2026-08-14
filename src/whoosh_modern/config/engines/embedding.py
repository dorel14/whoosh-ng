"""Engine for building an ``EmbeddingProvider`` from ``WhooshNGConfig.embedding``.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh_modern.config.models import WhooshNGConfig


class EmbeddingEngine:
    """Build an ``EmbeddingProvider`` from ``WhooshNGConfig.embedding``.

    Attributes:
        _config: The merged application configuration.
    """

    def __init__(self, config: WhooshNGConfig) -> None:
        """Initialize the engine with a merged configuration.

        Args:
            config: Merged Whoosh-NG configuration.
        """
        self._config = config

    def build(self) -> Any:
        """Build an EmbeddingProvider from the configured embedding settings.

        Returns:
            An EmbeddingProvider instance, or ``None`` if no embedding
            configuration is provided.
        """
        embedding_config = self._config.embedding
        if not embedding_config or not embedding_config.provider:
            return None
        provider_type = embedding_config.provider.lower()
        if provider_type == "fastembed":
            try:
                from whoosh_modern.embeddings.fastembed_provider import FastEmbedProvider

                return FastEmbedProvider(
                    model_name=embedding_config.model or "BAAI/bge-small-en-v1.5"
                )
            except ImportError as exc:
                raise ImportError(
                    "FastEmbedProvider requires fastembed. "
                    "Install with: pip install whoosh-ng[embeddings]"
                ) from exc
        if provider_type == "onnx":
            try:
                from whoosh_modern.embeddings.onnx_provider import ONNXEmbeddingProvider

                return ONNXEmbeddingProvider(
                    model_path=str(embedding_config.model_path or ""),
                    tokenizer_dir=embedding_config.tokenizer_dir,
                    pooling=embedding_config.pooling,
                    normalize=embedding_config.normalize,
                    quantization=embedding_config.quantization or "fp32",
                )
            except ImportError as exc:
                raise ImportError(
                    "ONNXEmbeddingProvider requires tokenizers and onnxruntime. "
                    "Install with: pip install whoosh-ng[embeddings-onnx]"
                ) from exc
        if provider_type == "sentence-transformers":
            try:
                from whoosh_modern.embeddings.sentence_transformers_provider import (
                    SentenceTransformersProvider,
                )

                return SentenceTransformersProvider(
                    model_name=embedding_config.model or "all-MiniLM-L6-v2"
                )
            except ImportError as exc:
                raise ImportError(
                    "SentenceTransformersProvider requires sentence-transformers. "
                    "Install with: pip install whoosh-ng[embeddings]"
                ) from exc
        raise ValueError(f"Unsupported embedding provider: {provider_type}")
