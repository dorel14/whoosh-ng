"""Synonym expansion middleware.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext
from whoosh_modern.linguistics.synonyms.manager import SynonymManager


class SynonymExpansionMiddleware(Middleware):
    """Expand queries and documents with synonyms.

    Args:
        manager: SynonymManager instance providing synonym lookups.
    """

    def __init__(self, manager: SynonymManager) -> None:
        """Initialize the middleware with a SynonymManager instance.

        Args:
            manager: The :class:`SynonymManager` used for synonym lookups
                during query and document expansion.
        """
        self._manager = manager

    def _expand_text(self, text: str) -> str:
        """Expand a text string by appending synonyms for each token.

        Args:
            text: The input text to expand.

        Returns:
            The original tokens followed by their synonyms, joined by spaces.
        """
        out: list[str] = []
        for tok in text.split():
            out.append(tok)
            syns = self._manager.get_synonyms(tok)
            out.extend(syns)
        return " ".join(out)

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Expand the query string in the search context with synonyms.

        Args:
            context: The middleware context containing the search query.

        Returns:
            The modified middleware context with an expanded query string.
        """
        if context.query:
            context.query = self._expand_text(context.query)
        return context

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Expand string document field values with synonyms before indexing.

        Args:
            context: The middleware context containing the document to index.

        Returns:
            The modified middleware context with expanded document field values.
        """
        doc = context.document
        if doc is None:
            return context
        for key, value in list(doc.items()):
            if isinstance(value, str):
                doc[key] = self._expand_text(value)
        return context
