"""Autocomplete extension plugin for Whoosh-NG.

Provides the AutocompletePlugin which registers itself with the plugin
manager and exposes an "inverted" provider in the autocomplete registry.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from typing import Any

from whoosh.hooks import hookimpl, register_hook
from whoosh.plugins.manager import Plugin
from whoosh.registry import AutocompleteRegistry
from whoosh_modern.autocomplete.factory import create_autocomplete


class AutocompletePlugin(Plugin):
    """Autocomplete plugin for Whoosh-NG.

    Registers itself in the autocomplete registry with the "inverted"
    provider and registers an ``on_search`` hook (no-op by default).
    """

    name = "whoosh_autocomplete"
    version = "5.0.0"

    def register(self, manager: Any) -> None:
        """Register the autocomplete provider in the registry.

        Args:
            manager: The Whoosh plugin manager.
        """
        AutocompleteRegistry.register("inverted", create_autocomplete("inverted"), self.name)

    def register_hooks(self) -> None:
        """Register autocomplete hooks."""

        def on_search(request: Any, response: Any) -> None:
            """Hook executed during a search (no-op)."""
            pass

        register_hook("on_search", hookimpl(on_search))


__all__ = ["AutocompletePlugin"]
