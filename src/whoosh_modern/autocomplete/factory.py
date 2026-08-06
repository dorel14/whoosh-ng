from __future__ import annotations

from typing import Any

from whoosh_modern.autocomplete.edge_ngram import InvertedIndexAutocomplete
from whoosh_modern.autocomplete.fuzzy import FuzzySuggestProvider
from whoosh_modern.autocomplete.ngram import NGramProvider
from whoosh_modern.autocomplete.provider import AutocompleteProvider


def create_autocomplete(provider: str = "inverted", **kwargs: Any) -> AutocompleteProvider:
    if provider == "inverted":
        return InvertedIndexAutocomplete()
    if provider == "ngram":
        return NGramProvider(**kwargs)
    if provider == "fuzzy":
        return FuzzySuggestProvider(**kwargs)
    raise ValueError(f"Unknown autocomplete provider: {provider}")
