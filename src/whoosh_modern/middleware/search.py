"""Search middleware: query rewriting and result ranking.

These subclass :class:`whoosh.middleware.base.Middleware` and plug into the
existing :class:`~whoosh.middleware.chain.MiddlewareChain` via the
``before_search`` / ``after_search`` hooks. A ``rewriter`` / ``ranker`` callable
is applied to the query string (``context.query``) and result payload
(``context.results``) respectively.

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

QueryRewriter = Callable[[str], str]
Ranker = Callable[[Any], Any]


class SearchMiddleware(Middleware):
    """Base class for search-time middleware.

    Subclasses customize search behaviour by overriding the ``before_search``
    and/or ``after_search`` hooks provided by :class:`whoosh.middleware.base.Middleware`.
    """


class QueryRewriteMiddleware(SearchMiddleware):
    """Rewrite the search query before execution.

    Args:
        rewriter: Callable ``str -> str`` applied to ``context.query``.
            When ``None``, the query is left unchanged.
    """

    def __init__(self, rewriter: QueryRewriter | None = None) -> None:
        self._rewriter = rewriter

    @property
    def rewriter(self) -> QueryRewriter | None:
        """The query-rewriting callable.

        Returns:
            The rewriter callable, or ``None`` if none was set.
        """
        return self._rewriter

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Rewrite ``context.query`` before the search is executed.

        Args:
            context: The middleware context containing the query and other
                search-time state.

        Returns:
            The context with ``context.query`` rewritten by the configured
            rewriter (if any and if a query is present).
        """
        if self._rewriter and context.query:
            context.query = self._rewriter(context.query)
        return context


class RankingMiddleware(SearchMiddleware):
    """Re-rank the search results after execution.

    Args:
        ranker: Callable applied to ``context.results`` (e.g. re-sort).
            When ``None``, results are left unchanged.
    """

    def __init__(self, ranker: Ranker | None = None) -> None:
        self._ranker = ranker

    @property
    def ranker(self) -> Ranker | None:
        """The result-ranking callable.

        Returns:
            The ranker callable, or ``None`` if none was set.
        """
        return self._ranker

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Re-rank ``context.results`` after the search has executed.

        Args:
            context: The middleware context containing the results and other
                search-time state.

        Returns:
            The context with ``context.results`` re-ranked by the configured
            ranker (if any and if results are present).
        """
        if self._ranker is not None and context.results is not None:
            context.results = self._ranker(context.results)
        return context


__all__ = [
    "SearchMiddleware",
    "QueryRewriteMiddleware",
    "RankingMiddleware",
    "QueryRewriter",
    "Ranker",
]
