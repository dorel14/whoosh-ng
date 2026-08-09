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

Author: dorel14
Version: 3.0.0
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Protocol, cast, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class StemmerProvider(Protocol):
    """Protocol for stemmer providers.

    A stemmer provider must implement ``stem`` and expose ``name``
    and ``language`` properties.
    """

    def stem(self, word: str) -> str:
        """Stem a single word.

        Args:
            word: The word to stem.

        Returns:
            The stemmed form of the word.
        """
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
    """Wrapper around Whoosh's internal stem function.

    Attributes:
        _language: The language code for this stemmer.
        _stem_fn: The resolved stem callable.
    """

    def __init__(self, language: str = "english") -> None:
        """Initialize the InternalStemmerProvider.

        Args:
            language: Language code for the stemmer (default: "english").
        """
        self._language = language
        self._stem_fn = self._load_stem_fn(language)

    def _load_stem_fn(self, language: str) -> Callable[[str], str]:
        """Load the appropriate stem function for the language.

        Tries the Whoosh ``porter`` stemmer first, then falls back to
        the legacy ``whoosh.analysis.stem``, and finally uses an
        identity function if no stemmer is available.

        Args:
            language: Language code (currently informational; porter is English-only).

        Returns:
            A callable that stems a single word.
        """
        try:
            from whoosh.lang import porter

            return porter.stem
        except ImportError:
            try:
                from whoosh.analysis import stem  # type: ignore[attr-defined]

                return cast(Callable[[str], str], stem)
            except ImportError:
                logger.warning(f"No internal stemmer found for {language}, using identity")
                return lambda x: x

    def stem(self, word: str) -> str:
        """Stem a word using the internal stemmer.

        Args:
            word: The word to stem.

        Returns:
            The stemmed word.
        """
        return self._stem_fn(word)

    @property
    def name(self) -> str:
        """Return the stemmer provider name ("internal")."""
        return "internal"

    @property
    def language(self) -> str:
        """Return the language code for this stemmer."""
        return self._language


class PyStemmerProvider:
    """Wrapper around PyStemmer.

    Attributes:
        _language: The language code for this stemmer.
        _stemmer: The underlying ``Stemmer.Stemmer`` instance.
    """

    def __init__(self, language: str = "english") -> None:
        """Initialize the PyStemmerProvider.

        Args:
            language: Language code for the stemmer (default: "english").

        Raises:
            ImportError: If PyStemmer is not installed.
        """
        self._language = language
        self._stemmer = self._load_stemmer(language)

    def _load_stemmer(self, language: str):
        """Load PyStemmer for the given language.

        Args:
            language: Language code to load the stemmer for.

        Returns:
            A ``Stemmer.Stemmer`` instance.

        Raises:
            ImportError: If PyStemmer is not installed.
        """
        try:
            import Stemmer

            return Stemmer.Stemmer(language)
        except ImportError:
            raise ImportError(
                "PyStemmer is not installed. Install it with: pip install whoosh-ng[fast-stemming]"
            ) from None

    def stem(self, word: str) -> str:
        """Stem a word using PyStemmer.

        Args:
            word: The word to stem.

        Returns:
            The stemmed word.
        """
        return cast(str, self._stemmer.stemWord(word))

    @property
    def name(self) -> str:
        """Return the stemmer provider name ("pystemmer")."""
        return "pystemmer"

    @property
    def language(self) -> str:
        """Return the language code for this stemmer."""
        return self._language


class IdentityStemmerProvider:
    """No-op stemmer for testing/compatibility.

    Always returns the input word unchanged.
    """

    def stem(self, word: str) -> str:
        """Return word unchanged.

        Args:
            word: The word to "stem".

        Returns:
            The word as-is.
        """
        return word

    @property
    def name(self) -> str:
        """Return the stemmer provider name ("identity")."""
        return "identity"

    @property
    def language(self) -> str:
        """Return the language code ("none")."""
        return "none"


_registry: dict[str, StemmerProvider] = {}


def register_stemmer(name: str) -> Callable:
    """Decorator to register a custom stemmer provider.

    Usage::

        @register_stemmer("my_stemmer")
        class MyStemmer:
            def stem(self, word):
                return word.lower()

    Args:
        name: The registry key under which to register the stemmer.

    Returns:
        A decorator that instantiates and registers the class, then
        returns the class unchanged.
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

    Args:
        backend: "auto", "internal", "pystemmer", or a registered name.
        language: Language code for the stemmer.

    Returns:
        A ``StemmerProvider`` instance.

    Raises:
        ValueError: If ``backend`` is not a recognized stemmer name.
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

    Args:
        language: Language code for the stemmer.

    Returns:
        A ``StemmerProvider`` instance (PyStemmer if available, otherwise
        InternalStemmerProvider).
    """
    try:
        import Stemmer

        _ = Stemmer  # mark as used for type checkers
        logger.info(f"Auto-detected PyStemmer for {language}")
        return PyStemmerProvider(language)
    except ImportError:
        logger.info(f"PyStemmer not available, using internal stemmer for {language}")
        return InternalStemmerProvider(language)


def list_available_backends() -> dict[str, str]:
    """List available stemmer backends.

    Returns:
        A dict mapping backend name to availability status string
        ("available", "not installed", or "registered").
    """
    backends = {
        "internal": "available",
        "pystemmer": "available" if _is_pystemmer_available() else "not installed",
    }
    backends.update({name: "registered" for name in _registry})
    return backends


def _is_pystemmer_available() -> bool:
    """Check if PyStemmer is available.

    Returns:
        True if PyStemmer can be imported, False otherwise.
    """
    try:
        import Stemmer

        _ = Stemmer  # mark as used for type checkers
        return True
    except ImportError:
        return False


def validate_stemmer_compatibility(
    provider: StemmerProvider,
    test_words: list[str],
) -> dict[str, Any]:
    """Validate stemmer compatibility with a list of test words.

    Args:
        provider: StemmerProvider to validate.
        test_words: List of words to test.

    Returns:
        A dict with compatibility report containing keys: ``provider``,
        ``language``, ``total_words``, ``successful``, ``failed``,
        and ``results``.
    """
    results = []
    for word in test_words:
        try:
            stemmed = provider.stem(word)
            results.append(
                {
                    "word": word,
                    "stemmed": stemmed,
                    "success": True,
                }
            )
        except Exception as e:
            results.append(
                {
                    "word": word,
                    "error": str(e),
                    "success": False,
                }
            )

    return {
        "provider": provider.name,
        "language": provider.language,
        "total_words": len(test_words),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results,
    }
