"""FastEmbed-based embedding provider.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from whoosh_modern.embeddings.protocol import EmbeddingProvider

if TYPE_CHECKING:
    from collections.abc import Sequence


class FastEmbedProvider:
    """Embedding provider backed by FastEmbed (CPU-only, zero PyTorch).

    Wraps ``fastembed.TextEmbedding`` behind the ``EmbeddingProvider`` protocol.
    Models are downloaded automatically on first use and cached by FastEmbed.

    Attributes:
        _model: The underlying FastEmbed ``TextEmbedding`` instance.
        _model_name: The FastEmbed model identifier.
        _dimension: Expected embedding dimension, inferred from the model.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        """Initialize the FastEmbed provider.

        Args:
            model_name: FastEmbed model identifier
                (default: ``"BAAI/bge-small-en-v1.5"``).

        Raises:
            ImportError: If ``fastembed`` is not installed.
        """
        self._model_name = model_name
        self._model = self._load_model(model_name)
        self._dimension = int(self._model.dim) if hasattr(self._model, "dim") else 384

    @staticmethod
    def _load_model(model_name: str) -> Any:
        """Load a FastEmbed TextEmbedding model.

        Args:
            model_name: FastEmbed model identifier.

        Returns:
            A FastEmbed ``TextEmbedding`` instance.

        Raises:
            ImportError: If ``fastembed`` is not installed.
        """
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise ImportError(
                "FastEmbedProvider requires fastembed. "
                "Install with: pip install whoosh-ng[embeddings]"
            ) from exc
        return TextEmbedding(model_name)

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimension

    def embed(self, text: str) -> list[float]:
        """Embed a single text.

        Args:
            text: Input text to embed.

        Returns:
            A list of floats representing the embedding vector.
        """
        result = self._model.embed([text])
        first = result[0] if isinstance(result, list) else next(iter(result))
        return [float(x) for x in first.tolist()]

    def embed_batch(self, texts: list[str]) -> list[Sequence[float]]:
        """Embed a batch of texts.

        Args:
            texts: List of input texts to embed.

        Returns:
            A list of embedding vectors.
        """
        if not texts:
            return []
        return [vec.tolist() for vec in self._model.embed(texts)]
