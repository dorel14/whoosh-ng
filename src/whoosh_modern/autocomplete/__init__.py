from __future__ import annotations

from whoosh_modern.autocomplete.factory import create_autocomplete
from whoosh_modern.autocomplete.fuzzy import FuzzySuggestProvider
from whoosh_modern.autocomplete.ngram import NGramProvider

__all__ = ["create_autocomplete", "NGramProvider", "FuzzySuggestProvider"]
