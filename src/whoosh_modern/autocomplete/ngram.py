"""N-gram based autocomplete provider."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from whoosh_modern.autocomplete.provider import AutocompleteHit, AutocompleteProvider


class NGramProvider(AutocompleteProvider):
    """Autocomplete provider based on character n-grams.

        Builds n-gram indexes from added phrases and retrieves candidates
        by matching prefix n-grams.

    Author: dorel14
    Version: 2.0.0
    """

    def __init__(self, n: int = 3) -> None:
        self._n = n
        self._phrases: list[str] = []
        self._ngram_index: dict[str, Counter[str]] = {}

    def add(self, phrases: Iterable[str]) -> None:
        """Index one or more phrases into the n-gram index.

        Args:
            phrases: Iterable of strings to index.
        """
        for phrase in phrases:
            self._phrases.append(phrase)
            for ngram in self._ngrams(phrase):
                self._ngram_index.setdefault(ngram, Counter())
                self._ngram_index[ngram][phrase] += 1

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
        """Search for phrases matching the prefix via n-grams.

        Args:
            prefix: Prefix to search for.
            limit: Maximum number of results to return.

        Returns:
            List of AutocompleteHit sorted by descending score.
        """
        if not prefix:
            return []
        prefix_ngrams = self._ngrams(prefix)
        scores: dict[str, float] = {}
        for ngram in prefix_ngrams:
            for phrase, count in self._ngram_index.get(ngram, {}).items():
                scores[phrase] = scores.get(phrase, 0.0) + count
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [AutocompleteHit(text=phrase, score=score) for phrase, score in ranked[:limit]]

    def _ngrams(self, text: str) -> list[str]:
        """Generate character n-grams from text.

        Args:
            text: Input text to generate n-grams from.

        Returns:
            List of lowercase n-gram substrings.
        """
        text = text.lower()
        return [text[i : i + self._n] for i in range(max(len(text) - self._n + 1, 0))]
