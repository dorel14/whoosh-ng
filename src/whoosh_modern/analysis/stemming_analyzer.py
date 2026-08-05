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
"""

from __future__ import annotations

from typing import Union

from whoosh.analysis import StemmingAnalyzer as WhooshStemmingAnalyzer
from whoosh_modern.analysis.stemmer_providers import (
    StemmerProvider,
    get_stemmer,
    list_available_backends,
)


def StemmingAnalyzer(
    expression=__import__("whoosh.analysis.tokenizers", fromlist=["default_pattern"]).default_pattern,
    stoplist=__import__("whoosh.analysis", fromlist=["STOP_WORDS"]).STOP_WORDS,
    minsize=2,
    maxsize=None,
    gaps=False,
    stemmer: Union[str, StemmerProvider] = "auto",
    ignore=None,
    cachesize=50000,
):
    """Enhanced StemmingAnalyzer with plugin support.

    :param expression: Regular expression pattern for tokenization
    :param stoplist: List of stop words
    :param minsize: Minimum word size
    :param maxsize: Maximum word size
    :param gaps: If True, split on expression instead of matching
    :param stemmer: Stemmer backend: "auto", "internal", "pystemmer", or provider
    :param ignore: Set of words to not stem
    :param cachesize: Maximum number of stemmed words to cache
    :returns: Composed analyzer pipeline
    """
    # Resolve stemmer parameter to a callable
    if isinstance(stemmer, str):
        stemfn = get_stemmer(stemmer, "english").stem
    elif hasattr(stemmer, "stem"):
        stemfn = stemmer.stem
    else:
        raise ValueError(
            f"stemmer must be a string or StemmerProvider, got {type(stemmer)}"
        )

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


__all__ = ["StemmingAnalyzer", "list_available_backends"]
