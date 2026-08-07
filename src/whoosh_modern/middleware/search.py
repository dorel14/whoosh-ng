"""Search middleware: query rewriting and result ranking.

These subclass :class:`whoosh.middleware.base.Middleware` and plug into the
existing :class:`~whoosh.middleware.chain.MiddlewareChain` via the
``before_search`` / ``after_search`` hooks. A ``rewriter`` / ``ranker`` callable
is applied to the query string (``context.query``) and result payload
(``context.results``) respectively.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

QueryRewriter = Callable[[str], str]
Ranker = Callable[[Any], Any]


class SearchMiddleware(Middleware):
    """Base class for search-time middleware."""


class QueryRewriteMiddleware(SearchMiddleware):
    """Rewrite the search query before execution.

    :param rewriter: callable ``str -> str`` applied to ``context.query``.
    """

    def __init__(self, rewriter: QueryRewriter | None = None) -> None:
        self._rewriter = rewriter

    @property
    def rewriter(self) -> QueryRewriter | None:
        return self._rewriter

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if self._rewriter and context.query:
            context.query = self._rewriter(context.query)
        return context


class RankingMiddleware(SearchMiddleware):
    """Re-rank the search results after execution.

    :param ranker: callable applied to ``context.results`` (e.g. re-sort).
    """

    def __init__(self, ranker: Ranker | None = None) -> None:
        self._ranker = ranker

    @property
    def ranker(self) -> Ranker | None:
        return self._ranker

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
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
