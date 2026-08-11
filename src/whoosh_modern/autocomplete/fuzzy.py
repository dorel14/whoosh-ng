"""Fuzzy autocomplete provider.

Candidate phrases are held in a sorted word list that is fed to a core
:class:`whoosh.spelling.ListCorrector`, so the edit-distance search
reuses Whoosh's Levenshtein automata (``whoosh.automata``) instead of a
private phrase store. ``rapidfuzz`` (optional extra) is used as an
alternative scorer when available.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from collections.abc import Iterable

from whoosh.spelling import Corrector, ListCorrector
from whoosh_modern.autocomplete.provider import AutocompleteHit, AutocompleteProvider


class FuzzySuggestProvider(AutocompleteProvider):
    """Fuzzy autocomplete provider based on :class:`whoosh.spelling.Corrector`.

    Suggestions are produced by a core ``ListCorrector`` (Levenshtein
    automaton). When the optional ``rapidfuzz`` dependency is installed
    it is used as an alternative, similarity-based scorer::

        pip install whoosh-ng[fuzzy]

    Args:
        max_distance: Maximum edit distance used by the corrector.
        score_cutoff: Minimum rapidfuzz score (0-100) to keep a match.

    Author: dorel14
    Version: 3.0.0
    """

    def __init__(self, max_distance: int = 2, score_cutoff: float = 50.0) -> None:
        self._max_distance = max_distance
        self._score_cutoff = score_cutoff
        self._phrases: list[str] = []
        self._corrector: Corrector | None = None

    def add(self, phrases: Iterable[str]) -> None:
        """Index one or more phrases.

        Args:
            phrases: Iterable of strings to index.
        """
        self._phrases.extend(phrases)
        self._corrector = None

    def corrector(self) -> Corrector:
        """Return the core corrector built from the indexed phrases.

        Returns:
            A :class:`whoosh.spelling.ListCorrector` over the sorted
            phrase list.
        """
        if self._corrector is None:
            self._corrector = ListCorrector(sorted(self._phrases))
        return self._corrector

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
        """Search for approximately matching phrases.

        Args:
            prefix: Search text to compare against.
            limit: Maximum number of results to return.

        Returns:
            List of AutocompleteHit sorted by descending score.
        """
        if not self._phrases:
            return []
        try:
            from rapidfuzz import fuzz, process
        except ImportError:
            return self._corrector_hits(prefix, limit)
        results = process.extract(
            prefix,
            self._phrases,
            scorer=fuzz.WRatio,
            limit=limit,
            score_cutoff=self._score_cutoff,
        )
        if results:
            return [AutocompleteHit(text=text, score=score / 100.0) for text, score, _ in results]
        return self._corrector_hits(prefix, limit)

    def _corrector_hits(self, prefix: str, limit: int) -> list[AutocompleteHit]:
        """Produce hits using the core corrector only.

        Args:
            prefix: Search text to compare against.
            limit: Maximum number of results to return.

        Returns:
            List of AutocompleteHit sorted by descending score.
        """
        sugs = self.corrector().suggest(prefix, limit=limit, maxdist=self._max_distance)
        total = float(len(sugs)) or 1.0
        return [
            AutocompleteHit(text=sug, score=(total - rank) / total) for rank, sug in enumerate(sugs)
        ]


__all__ = ["FuzzySuggestProvider"]
