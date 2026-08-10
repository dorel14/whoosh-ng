"""Factory for creating autocomplete providers.

Provides a unified interface to create different types of autocomplete
providers based on the desired backend.

Author: dorel14
Version: 2.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh_modern.autocomplete.fuzzy import FuzzySuggestProvider
from whoosh_modern.autocomplete.inverted import InvertedIndexAutocomplete
from whoosh_modern.autocomplete.ngram import NGramProvider
from whoosh_modern.autocomplete.provider import AutocompleteProvider


def create_autocomplete(provider: str = "inverted", **kwargs: Any) -> AutocompleteProvider:
    """Create an autocomplete provider of the specified type.

    Args:
        provider: Type of provider ("inverted", "ngram", or "fuzzy").
            - ``"inverted"``: prefix-based inverted autocomplete (default)
            - ``"ngram"``: character n-gram-based autocomplete
            - ``"fuzzy"``: approximate matching via rapidfuzz
        **kwargs: Additional arguments passed to the selected provider.

    Returns:
        An AutocompleteProvider instance.

    Raises:
        ValueError: If the provider type is unknown.
    """
    if provider == "inverted":
        return InvertedIndexAutocomplete()
    if provider == "ngram":
        return NGramProvider(**kwargs)
    if provider == "fuzzy":
        return FuzzySuggestProvider(**kwargs)
    raise ValueError(f"Unknown autocomplete provider: {provider}")
