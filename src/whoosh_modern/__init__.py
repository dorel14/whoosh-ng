from __future__ import annotations

from whoosh_modern.autocomplete.plugin import AutocompletePlugin

try:
    from whoosh_modern.vector.plugin import VectorPlugin
except ImportError:
    VectorPlugin = None

__all__ = ["AutocompletePlugin", "VectorPlugin"]
