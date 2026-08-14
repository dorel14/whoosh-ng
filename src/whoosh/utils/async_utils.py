"""Backward-compatible shim for ``whoosh.utils.async_utils``.

All names are re-exported from :mod:`whoosh.util.async_utils`. New code should
import from ``whoosh.util.async_utils`` directly.

Auteur: SoniqueBay Team
Version: 1.0.0
"""

from whoosh.util.async_utils import (  # noqa: F401
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
