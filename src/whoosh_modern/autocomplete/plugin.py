from __future__ import annotations

from whoosh.plugins.manager import Plugin
from whoosh.registry import AutocompleteRegistry
from whoosh_modern.autocomplete.factory import create_autocomplete


class AutocompletePlugin(Plugin):
    name = "whoosh_autocomplete"
    version = "4.0.0"

    def register(self, manager) -> None:
        AutocompleteRegistry.register("inverted", create_autocomplete("inverted"), self.name)


__all__ = ["AutocompletePlugin"]
