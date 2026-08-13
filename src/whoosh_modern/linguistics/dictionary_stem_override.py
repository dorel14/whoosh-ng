"""Dictionary stem override for custom stemming rules.

Allows overriding the Snowball stemmer with business dictionaries
(JSON/Wiktionary).

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations


class DictionaryStemOverride:
    """Stem override using custom dictionaries.

    Args:
        dictionary: Optional mapping of word -> stemmed form.
    """

    def __init__(self, dictionary: dict[str, str] | None = None) -> None:
        self._dictionary = dictionary or {}

    def stem(self, word: str) -> str:
        """Return the stemmed form of a word.

        If the word is in the dictionary, the dictionary form is returned.
        Otherwise, the word is returned unchanged.

        Args:
            word: The word to stem.

        Returns:
            The stemmed form.
        """
        return self._dictionary.get(word, word)

    def add_rule(self, word: str, stem: str) -> None:
        """Add a custom stemming rule.

        Args:
            word: The original word.
            stem: The stemmed form.
        """
        self._dictionary[word] = stem

    def load_dict(self, dictionary: dict[str, str]) -> None:
        """Load a complete dictionary of stemming rules.

        Args:
            dictionary: Mapping of word -> stemmed form.
        """
        self._dictionary.update(dictionary)


__all__ = ["DictionaryStemOverride"]
