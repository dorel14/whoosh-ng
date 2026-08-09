"""Fuzzy autocomplete provider using rapidfuzz (optional).

Uses rapidfuzz for approximate string matching when the ``fuzzy``
extra is installed.

Author: dorel14
Version: 2.0.0
"""

from __future__ import annotations

from collections.abc import Iterable

from whoosh_modern.autocomplete.provider import AutocompleteHit, AutocompleteProvider


class FuzzySuggestProvider(AutocompleteProvider):
    """Fuzzy autocomplete provider using rapidfuzz for approximate matching.

    rapidfuzz is an optional dependency. Install it with::

        pip install whoosh-ng[fuzzy]
    """

    def __init__(self, max_distance: int = 2, score_cutoff: float = 50.0) -> None:
        self._max_distance = max_distance
        self._score_cutoff = score_cutoff
        self._phrases: list[str] = []

    def add(self, phrases: Iterable[str]) -> None:
        """Index one or more phrases.

        Args:
            phrases: Iterable of strings to index.
        """
        self._phrases.extend(phrases)

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
        """Search for approximately matching phrases.

        Args:
            prefix: Search text to compare against.
            limit: Maximum number of results to return.

        Returns:
            List of AutocompleteHit sorted by descending score.

        Raises:
            ImportError: If rapidfuzz is not installed.
        """
        if not self._phrases:
            return []
        try:
            from rapidfuzz import fuzz, process
        except ImportError as exc:
            raise ImportError(
                "rapidfuzz is required for FuzzySuggestProvider. "
                "Install it with: pip install whoosh-ng[fuzzy]"
            ) from exc
        results = process.extract(
            prefix,
            self._phrases,
            scorer=fuzz.WRatio,
            limit=limit,
            score_cutoff=self._score_cutoff,
        )
        return [AutocompleteHit(text=text, score=score / 100.0) for text, score, _ in results]
