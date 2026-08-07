from __future__ import annotations

import pytest

from whoosh_modern.autocomplete.factory import create_autocomplete


@pytest.fixture
def autocomplete():
    ac = create_autocomplete("inverted")
    ac.add(
        [
            "machine learning",
            "machine vision",
            "macho man",
            "mackenzie",
        ]
    )
    return ac


def test_search_returns_matching_hits(autocomplete) -> None:
    hits = autocomplete.search("mach")
    texts = [hit.text for hit in hits]
    assert "macho man" in texts
    assert "machine learning" in texts
    assert "machine vision" in texts


def test_search_limit(autocomplete) -> None:
    hits = autocomplete.search("m", limit=2)
    assert len(hits) <= 2


def test_unknown_provider_raises() -> None:
    with pytest.raises(ValueError, match="Unknown autocomplete provider"):
        create_autocomplete("nonexistent")


class TestNGramProvider:
    def test_search_returns_matches(self):
        ac = create_autocomplete("ngram")
        ac.add(["machine learning", "machine vision", "macho man", "mackenzie"])
        hits = ac.search("mach")
        texts = [hit.text for hit in hits]
        assert "machine learning" in texts
        assert "machine vision" in texts

    def test_empty_prefix(self):
        ac = create_autocomplete("ngram")
        ac.add(["hello"])
        hits = ac.search("")
        assert hits == []

    def test_no_matches(self):
        ac = create_autocomplete("ngram")
        ac.add(["hello", "world"])
        hits = ac.search("zzz")
        assert hits == []


class TestFuzzySuggestProvider:
    def test_search_returns_matches(self):
        pytest.importorskip("rapidfuzz")
        ac = create_autocomplete("fuzzy")
        ac.add(["machine learning", "machine vision", "macho man"])
        hits = ac.search("machin")
        texts = [hit.text for hit in hits]
        assert "machine learning" in texts

    def test_empty_phrases(self):
        pytest.importorskip("rapidfuzz")
        ac = create_autocomplete("fuzzy")
        hits = ac.search("hello")
        assert hits == []
