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
