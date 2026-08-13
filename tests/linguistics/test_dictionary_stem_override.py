"""Tests for EPIC 6.7 Sprint LNG-6: DictionaryStemOverride."""

from __future__ import annotations

import pytest

from whoosh_modern.linguistics.dictionary_stem_override import DictionaryStemOverride


class TestDictionaryStemOverride:
    """Tests for DictionaryStemOverride."""

    def test_empty_dictionary_returns_word(self) -> None:
        override = DictionaryStemOverride()
        assert override.stem("maison") == "maison"

    def test_dictionary_lookup(self) -> None:
        override = DictionaryStemOverride({"voiture": "voitur"})
        assert override.stem("voiture") == "voitur"

    def test_add_rule(self) -> None:
        override = DictionaryStemOverride()
        override.add_rule("maison", "maison")
        assert override.stem("maison") == "maison"

    def test_load_dict(self) -> None:
        override = DictionaryStemOverride()
        override.load_dict({"chien": "chien"})
        assert override.stem("chien") == "chien"
