"""Tests for search middleware (query rewriting + ranking)."""

from __future__ import annotations

import pytest

from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.context import MiddlewareContext
from whoosh_modern.middleware import (
    QueryRewriteMiddleware,
    RankingMiddleware,
    SearchMiddleware,
)


def test_query_rewrite_middleware_transforms_query() -> None:
    mw = QueryRewriteMiddleware(rewriter=lambda q: q.upper())
    ctx = MiddlewareContext("search")
    ctx.query = "hello world"
    result = mw.before_search(ctx)
    assert result.query == "HELLO WORLD"


def test_query_rewrite_noop_without_rewriter() -> None:
    mw = QueryRewriteMiddleware()
    ctx = MiddlewareContext("search")
    ctx.query = "hello"
    assert mw.before_search(ctx).query == "hello"


def test_ranking_middleware_transforms_results() -> None:
    mw = RankingMiddleware(ranker=lambda results: list(reversed(results)))
    ctx = MiddlewareContext("search")
    ctx.results = [1, 2, 3]
    result = mw.after_search(ctx)
    assert result.results == [3, 2, 1]


def test_ranking_middleware_noop_without_ranker() -> None:
    mw = RankingMiddleware()
    ctx = MiddlewareContext("search")
    ctx.results = [1, 2, 3]
    assert mw.after_search(ctx).results == [1, 2, 3]


def test_search_middleware_is_base() -> None:
    mw = SearchMiddleware()
    ctx = MiddlewareContext("search")
    assert mw.before_search(ctx) is ctx


def test_search_middleware_in_chain() -> None:
    chain = MiddlewareChain(
        [
            QueryRewriteMiddleware(rewriter=lambda q: q.strip().lower()),
            RankingMiddleware(ranker=lambda r: sorted(r, reverse=True)),
        ]
    )
    ctx = MiddlewareContext("search")
    ctx.query = "  Banana "
    ctx.results = [3, 1, 2]
    ctx = chain.run_before("before_search", ctx)
    ctx = chain.run_after("after_search", ctx)
    assert ctx.query == "banana"
    assert ctx.results == [3, 2, 1]
