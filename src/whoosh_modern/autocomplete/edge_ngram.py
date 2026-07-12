from __future__ import annotations

from typing import Iterable

from whoosh_modern.autocomplete.provider import AutocompleteHit, AutocompleteProvider


class InvertedIndexAutocomplete(AutocompleteProvider):
    def __init__(self) -> None:
        self._phrases: list[str] = []

    def add(self, phrases: Iterable[str]) -> None:
        self._phrases.extend(phrases)

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
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
        base = 1.0 / (len(phrase) + 1.0)
        bonus = 1.5 if phrase.lower() == prefix else 1.0
        return base * bonus
