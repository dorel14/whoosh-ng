"""Analyzer middleware: stemming and synonym expansion.

These subclass :class:`whoosh.middleware.base.Middleware` and hook into the
indexing / search pipeline. :class:`StemmingMiddleware` transforms text fields
(and the query) through a stemmer callable; :class:`SynonymMiddleware` is a
placeholder that delegates to a synonym expander (the real synonym engine lands
in Sprint D / EPIC 6).

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import warnings
from collections.abc import Callable, Sequence

from whoosh.middleware.base import Middleware
from whoosh.middleware.context import MiddlewareContext

Stemmer = Callable[[str], str]
SynonymExpander = Callable[[str], list[str]]


class AnalyzerMiddleware(Middleware):
    """Base class for analysis-time middleware.

    Subclasses customize the text-analysis phase by overriding the
    ``before_index`` and/or ``before_search`` hooks.
    """


class StemmingMiddleware(AnalyzerMiddleware):
    """Apply a stemmer to text fields before indexing (and to the query).

    Args:
        stemmer: Callable ``str -> str`` applied to individual tokens/words.
        fields: Document field names to stem.  If ``None``, every ``str``
            value in the document is stemmed.
        stem_query: Also stem ``context.query`` before search.
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
        """The configured stemmer callable.

        Returns:
            The ``str -> str`` stemmer function.
        """
        return self._stemmer

    def _stem_text(self, text: str) -> str:
        """Apply the stemmer to every space-delimited token in *text*.

        Args:
            text: The input text to stem.

        Returns:
            A string of stemmed tokens joined by spaces.
        """
        return " ".join(self._stemmer(tok) for tok in text.split())

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Stem text fields in the document before indexing.

        Args:
            context: The middleware context containing the document and
                other indexing-time state.

        Returns:
            The context with text fields (or all ``str`` values when
            ``fields`` is ``None``) stemmed in-place.
        """
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
        """Stem ``context.query`` before search, unless disabled.

        Args:
            context: The middleware context containing the query and
                other search-time state.

        Returns:
            The context with ``context.query`` stemmed (if ``stem_query``
            is ``True`` and a query is present).
        """
        if self._stem_query and context.query:
            context.query = self._stem_text(context.query)
        return context


class SynonymMiddleware(AnalyzerMiddleware):
    """Expand queries / documents with synonyms (placeholder for Sprint D).

    .. deprecated::
        Use :class:`SynonymExpansionMiddleware` instead. This class is
        preserved for backward compatibility and will be removed in a future
        release.

    Args:
        expand: Callable ``str -> list[str]`` returning synonyms for a word.
            When ``None`` the middleware is a pass-through (the synonym engine
            will be injected in EPIC 6).
    """

    def __init__(self, expand: SynonymExpander | None = None) -> None:
        warnings.warn(
            "SynonymMiddleware is deprecated, use SynonymExpansionMiddleware instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self._expand = expand

    @property
    def expander(self) -> SynonymExpander | None:
        """The synonym-expansion callable.

        Returns:
            The ``str -> list[str]`` expander function, or ``None`` if none
            was set.
        """
        return self._expand

    def _expand_text(self, text: str) -> str:
        """Expand every token in *text* with its synonyms.

        Args:
            text: The input text to expand.

        Returns:
            A string where each original token is followed by its synonyms.
            If no expander is configured, *text* is returned unchanged.
        """
        if self._expand is None:
            return text
        out: list[str] = []
        for tok in text.split():
            out.append(tok)
            out.extend(self._expand(tok))
        return " ".join(out)

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        """Expand synonyms in ``context.query`` before search.

        Args:
            context: The middleware context containing the query and
                other search-time state.

        Returns:
            The context with ``context.query`` synonym-expanded (if an
            expander is configured and a query is present).
        """
        if self._expand is not None and context.query:
            context.query = self._expand_text(context.query)
        return context

    def before_index(self, context: MiddlewareContext) -> MiddlewareContext:
        """Expand synonyms in string-valued document fields before indexing.

        Args:
            context: The middleware context containing the document and
                other indexing-time state.

        Returns:
            The context with string document values synonym-expanded
            in-place (if an expander is configured and a document is
            present).
        """
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
