"""Enhanced StemmingAnalyzer with plugin support.

Provides:
- StemmingAnalyzer with stemmer parameter
- Auto-detection of PyStemmer
- Backward compatibility with existing code

Usage:
    from whoosh_modern.analysis import StemmingAnalyzer

    # Auto-detect best stemmer
    analyzer = StemmingAnalyzer(stemmer="auto")

    # Explicit internal stemmer
    analyzer = StemmingAnalyzer(stemmer="internal")

    # PyStemmer (requires pip install whoosh-ng[fast-stemming])
    analyzer = StemmingAnalyzer(stemmer="pystemmer")

    # Custom stemmer provider
    analyzer = StemmingAnalyzer(stemmer=my_custom_stemmer)

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

from whoosh.analysis import StemmingAnalyzer as WhooshStemmingAnalyzer
from whoosh_modern.analysis.stemmer_providers import (
    StemmerProvider,
    get_stemmer,
    list_available_backends,
)

_DEFAULT_PATTERN = __import__(
    "whoosh.analysis.tokenizers", fromlist=["default_pattern"]
).default_pattern
_DEFAULT_STOP_WORDS = __import__("whoosh.analysis", fromlist=["STOP_WORDS"]).STOP_WORDS


def stemming_analyzer(
    expression=_DEFAULT_PATTERN,
    stoplist=_DEFAULT_STOP_WORDS,
    minsize=2,
    maxsize=None,
    gaps=False,
    stemmer: str | StemmerProvider = "auto",
    language: str = "english",
    ignore=None,
    cachesize=50000,
):
    """Enhanced StemmingAnalyzer with plugin support.

    Creates a Whoosh StemmingAnalyzer with a configurable stemmer backend.

    Args:
        expression: Regular expression pattern for tokenization.
        stoplist: Set of stop words to filter out.
        minsize: Minimum word size to stem.
        maxsize: Maximum word size to stem.
        gaps: If True, split on expression instead of matching.
        stemmer: Stemmer backend: "auto", "internal", "pystemmer", or a
            custom StemmerProvider instance.
        language: Language code for the stemmer (default: "english").
        ignore: Set of words to not stem.
        cachesize: Maximum number of stemmed words to cache.

    Returns:
        A composed Whoosh StemmingAnalyzer instance.

    Raises:
        ValueError: If ``stemmer`` is neither a string nor a
            StemmerProvider-compatible object.
    """
    # Resolve stemmer parameter to a callable
    if isinstance(stemmer, str):
        stemfn = get_stemmer(stemmer, language).stem
    elif hasattr(stemmer, "stem"):
        stemfn = stemmer.stem
    else:
        raise ValueError(f"stemmer must be a string or StemmerProvider, got {type(stemmer)}")

    return WhooshStemmingAnalyzer(
        expression=expression,
        stoplist=stoplist,
        minsize=minsize,
        maxsize=maxsize,
        gaps=gaps,
        stemfn=stemfn,
        ignore=ignore,
        cachesize=cachesize,
    )


StemmingAnalyzer = stemming_analyzer

__all__ = ["StemmingAnalyzer", "list_available_backends"]
