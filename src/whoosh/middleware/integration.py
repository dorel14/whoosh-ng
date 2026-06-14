"""Middleware integration utilities for Whoosh-NG.

This module provides functions to integrate middleware into the indexing and search pipeline
without breaking existing APIs.
"""

from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.wrappers import MiddlewareWriter, MiddlewareSearcher
from whoosh.plugins.manager import PluginManager


def apply_middleware_to_writer(writer, middleware: list | None = None) -> MiddlewareWriter:
    """Wrap a writer with middleware.

    :param writer: The underlying IndexWriter to wrap
    :param middleware: Optional list of middleware instances. If None, loads from PluginManager.
    :returns: MiddlewareWriter wrapping the original writer
    """
    if middleware is None:
        chain = (
            PluginManager.get_middleware_chain()
            if hasattr(PluginManager, "_default") and PluginManager._default
            else MiddlewareChain()
        )
    else:
        chain = MiddlewareChain(middleware)
    return MiddlewareWriter(writer, chain)


def apply_middleware_to_searcher(searcher, middleware: list | None = None) -> MiddlewareSearcher:
    """Wrap a searcher with middleware.

    :param searcher: The underlying Searcher to wrap
    :param middleware: Optional list of middleware instances. If None, loads from PluginManager.
    :returns: MiddlewareSearcher wrapping the original searcher
    """
    if middleware is None:
        chain = (
            PluginManager.get_middleware_chain()
            if hasattr(PluginManager, "_default") and PluginManager._default
            else MiddlewareChain()
        )
    else:
        chain = MiddlewareChain(middleware)
    return MiddlewareSearcher(searcher, chain)
