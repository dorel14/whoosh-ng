"""Tests for analyzer middleware (stemming + synonym placeholder)."""

from __future__ import annotations

import pytest

from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.context import MiddlewareContext
from whoosh_modern.middleware import (
    AnalyzerMiddleware,
    StemmingMiddleware,
    SynonymMiddleware,
)


def _dummy_stemmer(word: str) -> str:
    return word[:3]


def test_stemming_middleware_stems_configured_fields() -> None:
    mw = StemmingMiddleware(stemmer=_dummy_stemmer, fields=["title"])
    ctx = MiddlewareContext("index")
    ctx.document = {"title": "running jumping", "body": "untouched"}
    result = mw.before_index(ctx)
    assert result.document["title"] == "run jum"
    assert result.document["body"] == "untouched"


def test_stemming_middleware_stems_all_string_fields_when_no_fields() -> None:
    mw = StemmingMiddleware(stemmer=_dummy_stemmer)
    ctx = MiddlewareContext("index")
    ctx.document = {"a": "running", "b": 42}
    result = mw.before_index(ctx)
    assert result.document["a"] == "run"
    assert result.document["b"] == 42


def test_stemming_middleware_stems_query() -> None:
    mw = StemmingMiddleware(stemmer=_dummy_stemmer, stem_query=True)
    ctx = MiddlewareContext("search")
    ctx.query = "running"
    result = mw.before_search(ctx)
    assert result.query == "run"


def test_analyzer_middleware_is_base() -> None:
    mw = AnalyzerMiddleware()
    ctx = MiddlewareContext("index")
    assert mw.before_index(ctx) is ctx


def test_synonym_middleware_placeholder_noop_without_expander() -> None:
    mw = SynonymMiddleware()
    ctx = MiddlewareContext("search")
    ctx.query = "car"
    assert mw.before_search(ctx).query == "car"


def test_synonym_middleware_expands_query() -> None:
    mw = SynonymMiddleware(expand=lambda w: ["auto"] if w == "car" else [])
    ctx = MiddlewareContext("search")
    ctx.query = "car"
    assert mw.before_search(ctx).query == "car auto"


def test_analyzer_middleware_in_chain() -> None:
    chain = MiddlewareChain(
        [
            StemmingMiddleware(stemmer=_dummy_stemmer, fields=["title"]),
            SynonymMiddleware(expand=lambda w: ["auto"] if w == "car" else []),
        ]
    )
    ctx = MiddlewareContext("search")
    ctx.query = "car running"
    ctx.document = {"title": "running car", "body": "car"}
    ctx = chain.run_before("before_index", ctx)
    ctx = chain.run_before("before_search", ctx)
    assert ctx.document["title"] == "run car auto"
    assert ctx.document["body"] == "car auto"
    assert ctx.query == "car auto run"
