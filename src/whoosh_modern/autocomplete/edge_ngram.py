"""Inverted index autocomplete provider (prefix matching).

Uses a simple prefix-matching approach for autocomplete. For each
indexed phrase, the search compares the provided prefix against the
beginning of each phrase.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from collections.abc import Iterable

from whoosh_modern.autocomplete.provider import AutocompleteHit, AutocompleteProvider


class InvertedIndexAutocomplete(AutocompleteProvider):
    """Prefix-matching autocomplete provider.

    Indexes phrases in a list and searches for those beginning with
    the given prefix. The score favors exact matches and shorter
    phrases.
    """

    def __init__(self) -> None:
        self._phrases: list[str] = []

    def add(self, phrases: Iterable[str]) -> None:
        """Index one or more phrases.

        Args:
            phrases: Iterable of strings to index.
        """
        self._phrases.extend(phrases)

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
        """Search for phrases starting with a prefix.

        Args:
            prefix: Prefix to search for.
            limit: Maximum number of results to return.

        Returns:
            List of AutocompleteHit sorted by descending score.
        """
        prefix_lower = prefix.lower()
        matches = []
        for phrase in self._phrases:
            if phrase.lower().startswith(prefix_lower):
                score = self._score(phrase, prefix_lower)
                matches.append(AutocompleteHit(text=phrase, score=score))
        matches.sort(key=lambda hit: hit.score, reverse=True)
        return matches[:limit]

    @staticmethod
    def _score(phrase: str, prefix: str) -> float:
        """Calculate a relevance score for a match.

        Args:
            phrase: The candidate phrase.
            prefix: The prefix being searched for.

        Returns:
            Relevance score (higher = more relevant).
        """
        base = 1.0 / (len(phrase) + 1.0)
        bonus = 1.5 if phrase.lower() == prefix else 1.0
        return base * bonus
