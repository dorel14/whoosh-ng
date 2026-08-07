"""Synonym provider protocol and in-memory implementation."""

from __future__ import annotations


class SynonymProvider:
    """Protocol for synonym providers.

    A synonym provider maps a word to a list of synonymous terms.
    """

    def get_synonyms(self, word: str) -> list[str]:
        """Return synonyms for the given word."""
        raise NotImplementedError

    def add_synonym(self, word: str, synonyms: list[str]) -> None:
        """Add synonyms for the given word."""
        raise NotImplementedError

    def remove_synonym(self, word: str, synonym: str) -> None:
        """Remove a synonym for the given word."""
        raise NotImplementedError


class StaticSynonymProvider:
    """In-memory synonym provider backed by a dict."""

    def __init__(self, mapping: dict[str, list[str]] | None = None) -> None:
        self._mapping: dict[str, set[str]] = {k: set(v) for k, v in (mapping or {}).items()}

    def get_synonyms(self, word: str) -> list[str]:
        return list(self._mapping.get(word, set()))

    def add_synonym(self, word: str, synonyms: list[str]) -> None:
        if word not in self._mapping:
            self._mapping[word] = set()
        self._mapping[word].update(synonyms)

    def remove_synonym(self, word: str, synonym: str) -> None:
        if word in self._mapping:
            self._mapping[word].discard(synonym)

    def to_dict(self) -> dict[str, list[str]]:
        return {k: list(v) for k, v in self._mapping.items()}

    def update_from_dict(self, data: dict[str, list[str]]) -> None:
        for word, syns in data.items():
            self.add_synonym(word, syns)
