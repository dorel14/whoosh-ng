"""Analyzer middleware: stemming and synonym expansion.

These subclass :class:`whoosh.middleware.base.Middleware` and hook into the
indexing / search pipeline. :class:`StemmingMiddleware` transforms text fields
(and the query) through a stemmer callable; :class:`SynonymMiddleware` is a
placeholder that delegates to a synonym expander (the real synonym engine lands
in Sprint D / EPIC 6).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

Stemmer = Callable[[str], str]
SynonymExpander = Callable[[str], list[str]]


class AnalyzerMiddleware(Middleware):
    """Base class for analysis-time middleware."""


class StemmingMiddleware(AnalyzerMiddleware):
    """Apply a stemmer to text fields before indexing (and to the query).

    :param stemmer: callable ``str -> str`` applied to individual tokens/words.
    :param fields: document field names to stem. If ``None``, every ``str``
        value in the document is stemmed.
    :param stem_query: also stem ``context.query`` before search.
    """

    def __init__(
        self,
        stemmer: Stemmer,
        fields: Sequence[str] | None = None,
        stem_query: bool = True,
    ) -> None:
        self._stemmer = stemmer
        self._fields = list(fields) if fields is not None else None
        self._stem_query = stem_query

    @property
    def stemmer(self) -> Stemmer:
        return self._stemmer

    def _stem_text(self, text: str) -> str:
        return " ".join(self._stemmer(tok) for tok in text.split())

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        doc = context.document
        if doc is None:
            return context
        if self._fields is None:
            for key, value in doc.items():
                if isinstance(value, str):
                    doc[key] = self._stem_text(value)
        else:
            for field in self._fields:
                if field in doc and isinstance(doc[field], str):
                    doc[field] = self._stem_text(doc[field])
        return context

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if self._stem_query and context.query:
            context.query = self._stem_text(context.query)
        return context


class SynonymMiddleware(AnalyzerMiddleware):
    """Expand queries / documents with synonyms (placeholder for Sprint D).

    :param expand: callable ``str -> list[str]`` returning synonyms for a word.
        When ``None`` the middleware is a pass-through (the synonym engine will
        be injected in EPIC 6).
    """

    def __init__(self, expand: SynonymExpander | None = None) -> None:
        self._expand = expand

    @property
    def expander(self) -> SynonymExpander | None:
        return self._expand

    def _expand_text(self, text: str) -> str:
        if self._expand is None:
            return text
        out: list[str] = []
        for tok in text.split():
            out.append(tok)
            out.extend(self._expand(tok))
        return " ".join(out)

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        if self._expand is not None and context.query:
            context.query = self._expand_text(context.query)
        return context

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        if self._expand is None:
            return context
        doc = context.document
        if doc is None:
            return context
        for key, value in list(doc.items()):
            if isinstance(value, str):
                doc[key] = self._expand_text(value)
        return context


__all__ = [
    "AnalyzerMiddleware",
    "StemmingMiddleware",
    "SynonymMiddleware",
    "Stemmer",
    "SynonymExpander",
]
