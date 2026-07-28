# mypy: ignore-errors
from __future__ import annotations

from whoosh_modern.autocomplete.plugin import AutocompletePlugin
from whoosh_modern.models import ModelIndex, SearchField

try:
    from whoosh_modern.vector.plugin import VectorPlugin
except ImportError:
    VectorPlugin = None

__all__ = ["AutocompletePlugin", "ModelIndex", "SearchField", "VectorPlugin"]
