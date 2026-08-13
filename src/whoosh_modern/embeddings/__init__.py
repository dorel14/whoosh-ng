"""Embedding providers package.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from whoosh_modern.embeddings.protocol import EmbeddingProvider
from whoosh_modern.embeddings.sentence_transformers_provider import (
    SentenceTransformersProvider,
)

__all__ = [
    "EmbeddingProvider",
    "SentenceTransformersProvider",
]
