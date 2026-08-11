"""Backwards-compatible alias for :mod:`whoosh_modern.autocomplete.inverted`.

The provider defined here never implemented edge n-grams; the module was
renamed to ``inverted.py``. This shim keeps the historical import path
working.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh_modern.autocomplete.inverted import InvertedIndexAutocomplete

__all__ = ["InvertedIndexAutocomplete"]
