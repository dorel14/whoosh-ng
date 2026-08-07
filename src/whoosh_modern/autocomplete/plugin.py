from __future__ import annotations

from typing import Any

from whoosh.hooks import hookimpl, register_hook
from whoosh.plugins.manager import Plugin
from whoosh.registry import AutocompleteRegistry
from whoosh_modern.autocomplete.factory import create_autocomplete


class AutocompletePlugin(Plugin):
    name = "whoosh_autocomplete"
    version = "4.1.0"

    def register(self, manager: Any) -> None:
        AutocompleteRegistry.register("inverted", create_autocomplete("inverted"), self.name)

    def register_hooks(self) -> None:
        def on_search(request: Any, response: Any) -> None:
            pass

        register_hook("on_search", hookimpl(on_search))


__all__ = ["AutocompletePlugin"]


__all__ = ["AutocompletePlugin"]
