"""Fuzzy autocomplete provider using rapidfuzz (optional)."""

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
        self._phrases.extend(phrases)

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
        if not self._phrases:
            return []
        try:
            from rapidfuzz import fuzz, process  # type: ignore[import-not-found]
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
