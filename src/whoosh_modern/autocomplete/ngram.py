"""N-gram based autocomplete provider.

The n-gram generation is delegated to :mod:`whoosh.analysis.ngrams`
(``NgramWordAnalyzer`` / ``NgramFilter`` / ``NgramTokenizer``) instead of
being re-implemented locally.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Any

from whoosh.analysis.ngrams import NgramWordAnalyzer
from whoosh_modern.autocomplete.provider import AutocompleteHit, AutocompleteProvider


class NGramProvider(AutocompleteProvider):
    """Autocomplete provider based on character n-grams.

    Builds n-gram indexes from added phrases using the core
    :func:`whoosh.analysis.ngrams.NgramWordAnalyzer` and retrieves
    candidates by matching the n-grams of the query prefix.

    Args:
        n: Size of the generated n-grams.
        at: Where to take n-grams from in each word. ``"start"`` (the
            default) produces edge n-grams, which is what autocomplete
            needs; ``None`` takes all n-grams.

    Author: dorel14
    Version: 3.0.0
    """

    def __init__(self, n: int = 3, at: str | None = "start") -> None:
        self._n = n
        self._at = at
        self._analyzer: Any = NgramWordAnalyzer(n, at=at)
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
        scores: dict[str, float] = {}
        for ngram in self._ngrams(prefix):
            for phrase, count in self._ngram_index.get(ngram, {}).items():
                scores[phrase] = scores.get(phrase, 0.0) + count
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [AutocompleteHit(text=phrase, score=score) for phrase, score in ranked[:limit]]

    def _ngrams(self, text: str) -> list[str]:
        """Generate n-grams from text using the core n-gram analyzer.

        Args:
            text: Input text to generate n-grams from.

        Returns:
            List of lowercase n-gram tokens.
        """
        if not text:
            return []
        return [token.text for token in self._analyzer(text)]


__all__ = ["NGramProvider"]
