from __future__ import annotations

from whoosh_modern.autocomplete.edge_ngram import InvertedIndexAutocomplete
from whoosh_modern.autocomplete.provider import AutocompleteProvider


def create_autocomplete(provider: str = "inverted") -> AutocompleteProvider:
    if provider == "inverted":
        return InvertedIndexAutocomplete()
    raise ValueError(f"Unknown autocomplete provider: {provider}")
