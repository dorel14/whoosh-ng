"""Embedding middleware for Whoosh-NG.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

logger = logging.getLogger(__name__)


class EmbeddingMiddleware(Middleware):
    """Middleware that enriches documents with embeddings before indexing.

    Uses an ``EmbeddingProvider`` to compute dense vectors for configured
    fields and stores them as ``STORED`` fields in the Whoosh index.
    Supports single or multiple field vectorization.

    Attributes:
        _embedding_provider: The embedding provider to use.
        _source_field: The default source field to read text from.
        _target_field: The default target field to store embeddings in.
        _batch_size: Maximum number of documents to embed in one batch.
        _embedding_fields: Sequence of source/target field pairs for
            multi-field embedding.
    """

    def __init__(
        self,
        embedding_provider: Any | None = None,
        source_field: str = "content",
        target_field: str = "embedding",
        batch_size: int = 32,
        embedding_fields: Sequence[dict[str, str]] | None = None,
    ) -> None:
        """Initialize the embedding middleware.

        Args:
            embedding_provider: An object exposing ``embed(text: str)`` and
                ``embed_batch(texts: list[str])``, or ``None`` to disable
                embedding enrichment.
            source_field: Default source field to embed when
                ``embedding_fields`` is not provided.
            target_field: Default target field when ``embedding_fields`` is
                not provided.
            batch_size: Maximum batch size for ``embed_batch`` calls.
            embedding_fields: Sequence of ``{"source_field": ..., "target_field": ...}``
                mappings for multi-field embedding. When provided, the
                ``source_field`` and ``target_field`` defaults are ignored.
        """
        self._embedding_provider = embedding_provider
        self._source_field = source_field
        self._target_field = target_field
        self._batch_size = batch_size
        self._embedding_fields = embedding_fields

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Enrich the document with embeddings before indexing.

        When ``embedding_provider`` is configured and the document contains
        the configured source fields, the middleware computes embeddings and
        stores them under their respective target fields.

        Args:
            context: The middleware context for the current indexing operation.

        Returns:
            The enriched middleware context.
        """
        if self._embedding_provider is None:
            return context

        doc = context.document or {}
        fields_to_embed = self._embedding_fields or [
            {"source_field": self._source_field, "target_field": self._target_field},
        ]

        for field_config in fields_to_embed:
            source = field_config["source_field"]
            target = field_config["target_field"]
            text = doc.get(source)
            if not text or not isinstance(text, str):
                continue
            try:
                vector = self._embedding_provider.embed(text)
                doc[target] = vector
            except Exception as exc:
                logger.warning("Embedding failed for field %r: %s", target, exc)

        context.document = doc
        return context
