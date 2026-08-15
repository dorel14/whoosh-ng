"""Embedding providers package.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from whoosh_modern.embeddings.protocol import EmbeddingProvider
from whoosh_modern.embeddings.registry import EmbeddingModelRegistry, get_default_registry
from whoosh_modern.embeddings.sentence_transformers_provider import (
    SentenceTransformersProvider,
)

if TYPE_CHECKING:
    from whoosh_modern.embeddings.model_manager import EmbeddingModelManager
    from whoosh_modern.embeddings.onnx_provider import ONNXEmbeddingProvider
else:
    try:
        from whoosh_modern.embeddings.onnx_provider import ONNXEmbeddingProvider
    except ImportError:
        ONNXEmbeddingProvider = None
    try:
        from whoosh_modern.embeddings.model_manager import EmbeddingModelManager
    except ImportError:
        EmbeddingModelManager = None

__all__ = [
    "EmbeddingProvider",
    "SentenceTransformersProvider",
    "ONNXEmbeddingProvider",
    "EmbeddingModelRegistry",
    "EmbeddingModelManager",
    "get_default_registry",
]
