"""Embedding provider protocol.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers.

    Providers take a text string and return a vector embedding.
    """

    def embed(self, text: str) -> Sequence[float]:
        """Embed the given text into a vector.

        Args:
            text: The text to embed.

        Returns:
            A sequence of floats representing the embedding vector.
        """
        ...
