"""Protocol and base implementation for autocomplete providers.

Defines the AutocompleteProvider interface that all autocomplete providers
must implement, along with the AutocompleteHit class representing a
single autocomplete result.

Author: dorel14
Version: 1.0.0
"""

from __future__ import annotations

from collections.abc import Iterable

from whoosh.plugins.manager import Plugin


class AutocompleteHit:
    """Represents a single autocomplete result.

    Attributes:
        text: The suggested text.
        score: Relevance score (higher = more relevant).
    """

    def __init__(self, text: str, score: float) -> None:
        self.text = text
        self.score = score


class AutocompleteProvider(Plugin):
    """Base interface for autocomplete providers.

    An autocomplete provider indexes phrases and allows searching them
    by prefix or by similarity.

    Subclasses must implement :meth:`add` and :meth:`search`.
    """

    def add(self, phrases: Iterable[str]) -> None:
        """Index one or more phrases for search.

        Args:
            phrases: Iterable of strings to index.
        """
        raise NotImplementedError

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
        """Search for phrases matching a prefix.

        Args:
            prefix: Prefix or search text.
            limit: Maximum number of results to return.

        Returns:
            List of AutocompleteHit sorted by descending score.
        """
        raise NotImplementedError
