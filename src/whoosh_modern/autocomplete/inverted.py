"""Inverted-index autocomplete provider built on core Whoosh prefix search.

This module delegates the actual suggestion algorithm to
:func:`whoosh.query.autocomplete.suggestions`, which walks the term
dictionary of a real Whoosh index instead of re-implementing prefix
matching by hand.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from whoosh.fields import ID, Schema
from whoosh.filedb.filestore import RamStorage
from whoosh.query.autocomplete import AutocompleteQuery, suggestions
from whoosh_modern.autocomplete.provider import AutocompleteHit, AutocompleteProvider

if TYPE_CHECKING:  # pragma: no cover - typing only
    from whoosh.index import Index

#: Name of the field holding the whole indexed phrase.
FIELDNAME = "phrase"


class InvertedIndexAutocomplete(AutocompleteProvider):
    """Prefix autocomplete provider backed by a real Whoosh index.

    Phrases are stored verbatim (lowercased) as single terms in a RAM
    index, and completion is delegated to
    :func:`whoosh.query.autocomplete.suggestions`. The score favours
    exact matches and shorter phrases, as before.

    Author: dorel14
    Version: 3.0.0
    """

    def __init__(self) -> None:
        self._phrases: list[str] = []
        self._originals: dict[str, str] = {}
        self._index: Index | None = None

    def add(self, phrases: Iterable[str]) -> None:
        """Index one or more phrases.

        Args:
            phrases: Iterable of strings to index.
        """
        for phrase in phrases:
            self._phrases.append(phrase)
            self._originals.setdefault(phrase.lower(), phrase)
        self._index = None

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
        """Search for phrases starting with a prefix.

        Args:
            prefix: Prefix to search for.
            limit: Maximum number of results to return.

        Returns:
            List of AutocompleteHit sorted by descending score.
        """
        if not self._phrases:
            return []
        prefix_lower = prefix.lower()
        ix = self._ensure_index()
        with ix.searcher() as searcher:
            terms = suggestions(
                searcher,
                FIELDNAME,
                prefix_lower,
                limit=max(len(self._originals), 1),
                scorer="alpha",
            )
        hits = [
            AutocompleteHit(
                text=self._originals.get(term, term),
                score=self._score(self._originals.get(term, term), prefix_lower),
            )
            for term in terms
        ]
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:limit]

    def query(self, prefix: str, fieldname: str = FIELDNAME) -> AutocompleteQuery:
        """Build a core :class:`~whoosh.query.autocomplete.AutocompleteQuery`.

        Args:
            prefix: Prefix to complete.
            fieldname: Target field name for the query.

        Returns:
            An ``AutocompleteQuery`` usable with any Whoosh searcher.
        """
        return AutocompleteQuery(fieldname, prefix.lower())

    def _ensure_index(self) -> Index:
        """Build (or reuse) the in-memory index of registered phrases.

        Returns:
            The Whoosh index holding one document per unique phrase.
        """
        if self._index is not None:
            return self._index
        schema = Schema(**{FIELDNAME: ID(stored=True)})
        storage: Any = RamStorage()
        ix = storage.create_index(schema)
        writer = ix.writer()
        for lowered in self._originals:
            writer.add_document(**{FIELDNAME: lowered})
        writer.commit()
        self._index = ix
        return ix

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


__all__ = ["InvertedIndexAutocomplete"]
