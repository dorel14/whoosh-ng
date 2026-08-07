"""Synonym compiler for precompiling raw synonym data."""

from __future__ import annotations


class SynonymCompiler:
    """Precompile raw synonym data into a fast lookup format.

    Usage::

        compiler = SynonymCompiler(raw_data)
        compiled = compiler.compile()
    """

    def __init__(self, data: dict[str, list[str]] | None = None) -> None:
        self._data: dict[str, list[str]] = dict(data or {})

    def compile(self) -> dict[str, list[str]]:
        """Return the compiled synonym mapping."""
        return dict(self._data)

    def add(self, word: str, synonyms: list[str]) -> None:
        self._data[word] = list(set(self._data.get(word, []) + synonyms))

    def merge(self, other: dict[str, list[str]]) -> None:
        for word, syns in other.items():
            self.add(word, syns)
