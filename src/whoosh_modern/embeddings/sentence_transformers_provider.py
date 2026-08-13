"""Optional sentence-transformers embedding provider.

Requires the optional ``sentence-transformers`` package::

    pip install whoosh-ng[embeddings]

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from collections.abc import Sequence


class SentenceTransformersProvider:
    """Embedding provider using ``sentence-transformers``.

    Args:
        model_name: The sentence-transformers model to use.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        """Initialize the provider.

        Args:
            model_name: The sentence-transformers model to use.

        Raises:
            ImportError: If ``sentence-transformers`` is not installed.
        """
        try:
            import sentence_transformers  # pyright: ignore[reportMissingImports,reportUnusedImport]
        except ImportError as exc:
            raise ImportError(
                "SentenceTransformersProvider requires sentence-transformers. "
                "Install it with: pip install whoosh-ng[embeddings]"
            ) from exc
        self._model_name = model_name

    def embed(self, text: str) -> Sequence[float]:
        """Embed the given text into a vector.

        Args:
            text: The text to embed.

        Returns:
            A sequence of floats representing the embedding vector.
        """
        from sentence_transformers import (
            SentenceTransformer,  # pyright: ignore[reportMissingImports]
        )

        model = SentenceTransformer(self._model_name)
        embedding = model.encode(text, convert_to_numpy=True)
        return [float(v) for v in embedding.tolist()]
