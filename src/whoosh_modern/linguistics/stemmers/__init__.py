"""Whoosh-NG language-specific analyzers.

Provides ready-to-use analyzers for FR/EN/DE/ES/IT. These are thin aliases over
:func:`whoosh.analysis.analyzers.LanguageAnalyzer`, which already composes a
``RegexTokenizer``, ``LowercaseFilter``, a language-aware ``StopFilter`` and a
language-aware ``StemFilter`` (Snowball). Using the core analyzer fixes a bug in
the previous hand-rolled implementations, where non-English text was silently
stemmed with the English Porter algorithm.

Each name is an *instance* of :class:`_LanguageAnalyzerAlias`, a thin
``CompositeAnalyzer`` subclass, ready to be passed to a schema field or called
directly with text::

    tokens = [t.text for t in FrenchAnalyzer("les maisons")]

For backward compatibility with the historical, hand-rolled implementations
(where these names used to be *classes* that callers instantiated before
calling), calling one of these aliases with no arguments returns a fresh
analyzer instance rather than analyzing an empty string. This keeps
class-style usage working unchanged::

    tokens = [t.text for t in FrenchAnalyzer()("les maisons")]

Author: dorel14
Version: 3.1.0
"""

from __future__ import annotations

from re import Pattern
from typing import Any

from whoosh.analysis.analyzers import CompositeAnalyzer, LanguageAnalyzer
from whoosh.analysis.tokenizers import default_pattern


class _LanguageAnalyzerAlias(CompositeAnalyzer):
    """Callable, re-instantiable alias over :func:`LanguageAnalyzer`.

    Instances behave exactly like the :class:`CompositeAnalyzer` returned by
    :func:`whoosh.analysis.analyzers.LanguageAnalyzer` when called with text
    (e.g. ``FrenchAnalyzer("les maisons")`` or when used directly as a schema
    field analyzer), so existing "instance-style" usage keeps working.

    Additionally, calling the alias with *no* arguments mimics the historical
    class-based API, where these names used to be classes and callers wrote
    ``FrenchAnalyzer()(text)``. In that case, a fresh alias bound to the same
    language configuration is returned instead of attempting to analyze an
    empty string, so ``FrenchAnalyzer()(text)`` keeps working unchanged.
    """

    def __init__(
        self,
        lang: str,
        expression: Pattern[str] = default_pattern,
        gaps: bool = False,
        cachesize: int = 50000,
    ) -> None:
        """Initialize the alias for the given language configuration.

        Args:
            lang: The language code (e.g. ``"fr"``, ``"en"``).
            expression: The regular expression pattern used to extract tokens.
            gaps: If True, the tokenizer splits on ``expression`` instead of
                matching on it.
            cachesize: Size of the stemmer cache used by the underlying
                ``StemFilter``.
        """
        self._lang_args: tuple[str, Pattern[str], bool, int] = (lang, expression, gaps, cachesize)
        composed = LanguageAnalyzer(lang, expression, gaps, cachesize)
        super().__init__(*composed.items)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Analyze text, or construct a fresh alias when called with no args.

        Args:
            *args: Positional arguments. When empty (together with no
                keyword arguments), a new alias instance is returned instead
                of analyzing text, preserving the historical
                ``FrenchAnalyzer()(text)`` calling convention.
            **kwargs: Keyword arguments forwarded to the underlying
                ``CompositeAnalyzer.__call__`` (e.g. ``no_morph``).

        Returns:
            Either a new :class:`_LanguageAnalyzerAlias` (constructor-style
            call) or a generator of tokens (analyzer-style call).
        """
        if not args and not kwargs:
            return _LanguageAnalyzerAlias(*self._lang_args)
        return super().__call__(*args, **kwargs)


FrenchAnalyzer = _LanguageAnalyzerAlias("fr")
"""French analyzer (lowercase + French stopwords + French Snowball stemmer)."""

EnglishAnalyzer = _LanguageAnalyzerAlias("en")
"""English analyzer (lowercase + English stopwords + English Snowball stemmer)."""

GermanAnalyzer = _LanguageAnalyzerAlias("de")
"""German analyzer (lowercase + German stopwords + German Snowball stemmer)."""

SpanishAnalyzer = _LanguageAnalyzerAlias("es")
"""Spanish analyzer (lowercase + Spanish stopwords + Spanish Snowball stemmer)."""

ItalianAnalyzer = _LanguageAnalyzerAlias("it")
"""Italian analyzer (lowercase + Italian stopwords + Italian Snowball stemmer)."""

__all__ = [
    "FrenchAnalyzer",
    "EnglishAnalyzer",
    "GermanAnalyzer",
    "SpanishAnalyzer",
    "ItalianAnalyzer",
]
