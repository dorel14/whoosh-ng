"""Backward-compatible shim for ``whoosh.utils``.

All public names are re-exported from :mod:`whoosh.util`. New code should
import from ``whoosh.util`` directly; this shim preserves existing imports
such as ``from whoosh.utils import run_sync``.

Auteur: SoniqueBay Team
Version: 1.0.0
"""

from whoosh.util.async_utils import (
    call_maybe_async,
    is_async_callable,
    maybe_await,
    run_async_from_sync,
    run_sync,
)

__all__ = [
    "run_sync",
    "maybe_await",
    "call_maybe_async",
    "is_async_callable",
    "run_async_from_sync",
]
