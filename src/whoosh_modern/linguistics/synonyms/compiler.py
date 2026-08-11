"""Synonym compiler for precompiling raw synonym data.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations


class SynonymCompiler:
    """Precompile raw synonym data into a fast lookup format.

    Usage::

        compiler = SynonymCompiler(raw_data)
        compiled = compiler.compile()
    """

    def __init__(self, data: dict[str, list[str]] | None = None) -> None:
        """Initialize the compiler with optional raw synonym data.

        Args:
            data: A dict mapping words to lists of synonym terms.
                Defaults to an empty dict.
        """
        self._data: dict[str, list[str]] = dict(data or {})

    def compile(self) -> dict[str, list[str]]:
        """Return the compiled synonym mapping.

        Returns:
            A dict mapping each word to a list of its synonym terms.
        """
        return dict(self._data)

    def add(self, word: str, synonyms: list[str]) -> None:
        """Add synonyms for a word, deduplicating existing entries.

        Args:
            word: The term to associate synonyms with.
            synonyms: The list of synonym terms to add.
        """
        self._data[word] = list(set(self._data.get(word, []) + synonyms))

    def merge(self, other: dict[str, list[str]]) -> None:
        """Merge another synonym dict into the compiled data.

        Args:
            other: A dict mapping words to lists of synonym terms to merge.
        """
        for word, syns in other.items():
            self.add(word, syns)
