"""Synonym expansion middleware."""

from __future__ import annotations

from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext
from whoosh_modern.linguistics.synonyms.manager import SynonymManager


class SynonymExpansionMiddleware(Middleware):
    """Expand queries and documents with synonyms.

    :param manager: SynonymManager instance providing synonym lookups.
    """

    def __init__(self, manager: SynonymManager) -> None:
        self._manager = manager

    def _expand_text(self, text: str) -> str:
        out: list[str] = []
        for tok in text.split():
            out.append(tok)
            syns = self._manager.get_synonyms(tok)
            out.extend(syns)
        return " ".join(out)

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if context.query:
            context.query = self._expand_text(context.query)
        return context

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        doc = context.document
        if doc is None:
            return context
        for key, value in list(doc.items()):
            if isinstance(value, str):
                doc[key] = self._expand_text(value)
        return context
