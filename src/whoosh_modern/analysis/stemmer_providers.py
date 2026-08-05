"""Stemmer provider plugin system for Whoosh-NG.

Provides:
- StemmerProvider protocol
- InternalStemmerProvider
- PyStemmerProvider
- Auto-detection logic
- Compatibility validation

Usage:
    from whoosh_modern.analysis import get_stemmer, register_stemmer

    # Auto-detect best available stemmer
    stemfn = get_stemmer("auto", "english")
    analyzer = StemmingAnalyzer(stemfn=stemfn)

    # Explicit provider
    stemfn = get_stemmer("pystemmer", "english")
    analyzer = StemmingAnalyzer(stemfn=stemfn)

    # Register custom stemmer
    @register_stemmer("my_stemmer")
    class MyStemmer:
        def stem(self, word):
            return word.lower()

    analyzer = StemmingAnalyzer(stemmer="my_stemmer")
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class StemmerProvider(Protocol):
    """Protocol for stemmer providers."""

    def stem(self, word: str) -> str:
        """Stem a single word."""
        ...

    @property
    def name(self) -> str:
        """Return the stemmer name."""
        ...

    @property
    def language(self) -> str:
        """Return the language code."""
        ...


class InternalStemmerProvider:
    """Wrapper around Whoosh's internal stem function."""

    def __init__(self, language: str = "english") -> None:
        self._language = language
        self._stem_fn = self._load_stem_fn(language)

    def _load_stem_fn(self, language: str) -> Callable:
        """Load the appropriate stem function for the language."""
        try:
            from whoosh.lang import porter
            return porter.stem
        except ImportError:
            try:
                from whoosh.analysis import stem
                return stem
            except ImportError:
                logger.warning(f"No internal stemmer found for {language}, using identity")
                return lambda x: x

    def stem(self, word: str) -> str:
        """Stem a word using the internal stemmer."""
        return self._stem_fn(word)

    @property
    def name(self) -> str:
        return "internal"

    @property
    def language(self) -> str:
        return self._language


class PyStemmerProvider:
    """Wrapper around PyStemmer."""

    def __init__(self, language: str = "english") -> None:
        self._language = language
        self._stemmer = self._load_stemmer(language)

    def _load_stemmer(self, language: str):
        """Load PyStemmer for the given language."""
        try:
            import Stemmer
            return Stemmer.Stemmer(language)
        except ImportError:
            raise ImportError(
                "PyStemmer is not installed. "
                "Install it with: pip install whoosh-ng[fast-stemming]"
            )

    def stem(self, word: str) -> str:
        """Stem a word using PyStemmer."""
        return self._stemmer.stem(word)

    @property
    def name(self) -> str:
        return "pystemmer"

    @property
    def language(self) -> str:
        return self._language


class IdentityStemmerProvider:
    """No-op stemmer for testing/compatibility."""

    def stem(self, word: str) -> str:
        """Return word unchanged."""
        return word

    @property
    def name(self) -> str:
        return "identity"

    @property
    def language(self) -> str:
        return "none"


_registry: Dict[str, StemmerProvider] = {}


def register_stemmer(name: str) -> Callable:
    """Decorator to register a custom stemmer provider.
    
    Usage:
        @register_stemmer("my_stemmer")
        class MyStemmer:
            def stem(self, word):
                return word.lower()
    """
    def decorator(cls):
        _registry[name] = cls()
        return cls
    return decorator


def get_stemmer(
    backend: str = "auto",
    language: str = "english",
) -> StemmerProvider:
    """Get a stemmer provider by backend name.
    
    :param backend: "auto", "internal", "pystemmer", or registered name
    :param language: language code for the stemmer
    :returns: StemmerProvider instance
    """
    if backend == "auto":
        return _auto_detect(language)
    elif backend == "internal":
        return InternalStemmerProvider(language)
    elif backend == "pystemmer":
        return PyStemmerProvider(language)
    elif backend in _registry:
        return _registry[backend]
    else:
        raise ValueError(f"Unknown stemmer backend: {backend}")


def _auto_detect(language: str = "english") -> StemmerProvider:
    """Auto-detect the best available stemmer.
    
    Priority:
    1. PyStemmer (fastest)
    2. Internal stemmer (fallback)
    """
    try:
        import Stemmer
        logger.info(f"Auto-detected PyStemmer for {language}")
        return PyStemmerProvider(language)
    except ImportError:
        logger.info(f"PyStemmer not available, using internal stemmer for {language}")
        return InternalStemmerProvider(language)


def list_available_backends() -> Dict[str, str]:
    """List available stemmer backends.
    
    :returns: dict of backend name -> availability status
    """
    backends = {
        "internal": "available",
        "pystemmer": "available" if _is_pystemmer_available() else "not installed",
    }
    backends.update({name: "registered" for name in _registry})
    return backends


def _is_pystemmer_available() -> bool:
    """Check if PyStemmer is available."""
    try:
        import Stemmer
        return True
    except ImportError:
        return False


def validate_stemmer_compatibility(
    provider: StemmerProvider,
    test_words: list[str],
) -> Dict[str, Any]:
    """Validate stemmer compatibility with a list of test words.
    
    :param provider: StemmerProvider to validate
    :param test_words: list of words to test
    :returns: dict with compatibility report
    """
    results = []
    for word in test_words:
        try:
            stemmed = provider.stem(word)
            results.append({
                "word": word,
                "stemmed": stemmed,
                "success": True,
            })
        except Exception as e:
            results.append({
                "word": word,
                "error": str(e),
                "success": False,
            })

    return {
        "provider": provider.name,
        "language": provider.language,
        "total_words": len(test_words),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results,
    }
