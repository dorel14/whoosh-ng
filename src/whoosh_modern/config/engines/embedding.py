"""Engine for building an ``EmbeddingProvider`` from ``WhooshNGConfig.embedding``.

Author: dorel14
Version: 3.1.0
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from whoosh_modern.config.models import WhooshNGConfig

logger = logging.getLogger(__name__)


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
            logger.warning(
                "No embedding provider configured. Embeddings will not be generated. "
                "Set embedding.provider in your config to enable embeddings."
            )
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

                if embedding_config.model_path:
                    # Explicit local paths take precedence over any model name.
                    model_path = embedding_config.model_path
                    tokenizer_dir = embedding_config.tokenizer_dir
                elif embedding_config.model:
                    # Resolve a registered model name via EmbeddingModelManager,
                    # which downloads and caches the ONNX model files, then
                    # derives model_path and tokenizer_dir from the local cache.
                    from whoosh_modern.embeddings.model_manager import (
                        EmbeddingModelManager,
                    )

                    manager = EmbeddingModelManager()
                    model_dir = manager.download(
                        embedding_config.model,
                        expected_sha256=embedding_config.expected_sha256,
                    )
                    model_path = str(_resolve_onnx_path(model_dir))
                    tokenizer_dir = (
                        str(model_dir)
                        if embedding_config.tokenizer_dir is None
                        else embedding_config.tokenizer_dir
                    )
                    logger.info("ONNX model %r ready at %s", embedding_config.model, model_path)
                else:
                    raise ValueError(
                        "ONNX provider requires either 'model_path' (explicit local "
                        "paths) or 'model' (a registered model name resolved via "
                        "EmbeddingModelManager)."
                    )

                return ONNXEmbeddingProvider(
                    model_path=model_path,
                    tokenizer_dir=tokenizer_dir,
                    pooling=embedding_config.pooling,
                    normalize=embedding_config.normalize,
                    dimension=None,
                    enable_prefix=True,
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


def _resolve_onnx_path(model_dir: Path) -> Path:
    """Find the primary ``.onnx`` file inside a downloaded model directory.

    Args:
        model_dir: The directory where the model was downloaded/cached.

    Returns:
        The path to the first ``.onnx`` file found.

    Raises:
        FileNotFoundError: If no ``.onnx`` file is found in the directory.
    """
    onnx_files = sorted(model_dir.glob("*.onnx"))
    if not onnx_files:
        raise FileNotFoundError(f"No .onnx file found in {model_dir} after model download.")
    return onnx_files[0]
