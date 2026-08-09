"""Autocomplete management module for Whoosh-NG.

Provides the following autocomplete providers:
- NGramProvider: character n-gram based matching
- FuzzySuggestProvider: approximate matching via rapidfuzz
- InvertedIndexAutocomplete: inverted prefix autocomplete

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh_modern.autocomplete.factory import create_autocomplete
from whoosh_modern.autocomplete.fuzzy import FuzzySuggestProvider
from whoosh_modern.autocomplete.ngram import NGramProvider

__all__ = ["create_autocomplete", "NGramProvider", "FuzzySuggestProvider"]
