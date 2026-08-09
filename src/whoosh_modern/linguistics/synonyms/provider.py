"""Synonym provider protocol and in-memory implementation.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations


class SynonymProvider:
    """Protocol for synonym providers.

    A synonym provider maps a word to a list of synonymous terms.
    """

    def get_synonyms(self, word: str) -> list[str]:
        """Return synonyms for the given word.

        Args:
            word: The term whose synonyms should be retrieved.

        Returns:
            A list of synonymous terms. Returns an empty list if no
            synonyms exist for ``word``.

        Raises:
            NotImplementedError: Always, as this is a protocol method.
        """
        raise NotImplementedError

    def add_synonym(self, word: str, synonyms: list[str]) -> None:
        """Add synonyms for the given word.

        Args:
            word: The term to associate synonyms with.
            synonyms: The list of synonym terms to add.

        Raises:
            NotImplementedError: Always, as this is a protocol method.
        """
        raise NotImplementedError

    def remove_synonym(self, word: str, synonym: str) -> None:
        """Remove a synonym for the given word.

        Args:
            word: The term whose synonym should be removed.
            synonym: The synonym term to remove.

        Raises:
            NotImplementedError: Always, as this is a protocol method.
        """
        raise NotImplementedError


class StaticSynonymProvider:
    """In-memory synonym provider backed by a dict."""

    def __init__(self, mapping: dict[str, list[str]] | None = None) -> None:
        """Initialize the provider with an optional synonym mapping.

        Args:
            mapping: A dict mapping words to lists of synonym terms.
                Defaults to an empty mapping.
        """
        self._mapping: dict[str, set[str]] = {k: set(v) for k, v in (mapping or {}).items()}

    def get_synonyms(self, word: str) -> list[str]:
        """Return synonyms for the given word.

        Args:
            word: The term whose synonyms should be retrieved.

        Returns:
            A list of synonymous terms. Returns an empty list if no
            synonyms exist for ``word``.
        """
        return list(self._mapping.get(word, set()))

    def add_synonym(self, word: str, synonyms: list[str]) -> None:
        """Add synonyms for the given word.

        Args:
            word: The term to associate synonyms with.
            synonyms: The list of synonym terms to add.
        """
        if word not in self._mapping:
            self._mapping[word] = set()
        self._mapping[word].update(synonyms)

    def remove_synonym(self, word: str, synonym: str) -> None:
        """Remove a synonym for the given word.

        Args:
            word: The term whose synonym should be removed.
            synonym: The synonym term to remove.
        """
        if word in self._mapping:
            self._mapping[word].discard(synonym)

    def to_dict(self) -> dict[str, list[str]]:
        """Convert the internal mapping to a serializable dict.

        Returns:
            A dict mapping each word to a list of its synonym terms.
        """
        return {k: list(v) for k, v in self._mapping.items()}

    def update_from_dict(self, data: dict[str, list[str]]) -> None:
        """Merge synonyms from a dict into the internal mapping.

        Args:
            data: A dict mapping words to lists of synonym terms to merge.
        """
        for word, syns in data.items():
            self.add_synonym(word, syns)
