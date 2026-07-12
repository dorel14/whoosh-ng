from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from whoosh.index import Index

from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.context import MiddlewareContext


class MiddlewareWriter:
    """Wrapper for IndexWriter that executes middleware hooks.

    This wrapper intercepts add_document, update_document, delete_document,
    and commit calls to run middleware before/after operations.
    """

    def __init__(self, writer: Any, chain: MiddlewareChain) -> None:
        self._writer = writer
        self._chain = chain

    def add_document(self, **fields) -> None:
        ctx = MiddlewareContext("add_document")
        ctx.document = dict(fields)
        ctx = self._chain.run_before("before_index", ctx)
        try:
            self._writer.add_document(**ctx.document)
            ctx = self._chain.run_after("after_index", ctx)
        except Exception as exc:
            self._chain.run_on_error(ctx, exc)
            raise

    def update_document(self, **fields) -> None:
        ctx = MiddlewareContext("update_document")
        ctx.document = dict(fields)
        ctx = self._chain.run_before("before_index", ctx)
        try:
            self._writer.update_document(**ctx.document)
            ctx = self._chain.run_after("after_index", ctx)
        except Exception as exc:
            self._chain.run_on_error(ctx, exc)
            raise

    def delete_document(self, docnum: int | None = None, term: Any = None, **kwargs) -> None:
        ctx = MiddlewareContext("delete_document")
        ctx.metadata["docnum"] = docnum
        ctx.metadata["term"] = term
        ctx = self._chain.run_before("before_delete", ctx)
        try:
            self._writer.delete_document(docnum, term, **kwargs)
            ctx = self._chain.run_after("after_delete", ctx)
        except Exception as exc:
            self._chain.run_on_error(ctx, exc)
            raise

    def commit(self) -> None:
        ctx = MiddlewareContext("commit")
        try:
            self._writer.commit()
            ctx = self._chain.run_after("on_commit", ctx)
        except Exception as exc:
            self._chain.run_on_error(ctx, exc)
            raise

    def cancel(self) -> None:
        self._writer.cancel()

    def __enter__(self) -> MiddlewareWriter:
        return self

    def __exit__(self, *args) -> None:
        self._writer.__exit__(*args)


class MiddlewareSearcher:
    """Wrapper for Searcher that executes middleware hooks on search operations."""

    def __init__(self, searcher: Any, chain: MiddlewareChain) -> None:
        self._searcher = searcher
        self._chain = chain

    def search(self, query: Any, **kwargs) -> Any:
        ctx = MiddlewareContext("search")
        ctx.query = str(query)
        ctx = self._chain.run_before("before_search", ctx)
        try:
            results = self._searcher.search(query, **kwargs)
            ctx.results = results
            ctx = self._chain.run_after("after_search", ctx)
            return ctx.results
        except Exception as exc:
            self._chain.run_on_error(ctx, exc)
            raise

    def search_page(self, query: Any, pagenum: int, **kwargs) -> Any:
        ctx = MiddlewareContext("search_page")
        ctx.query = str(query)
        ctx.metadata["pagenum"] = pagenum
        ctx = self._chain.run_before("before_search", ctx)
        try:
            results = self._searcher.search_page(query, pagenum, **kwargs)
            ctx.results = results
            ctx = self._chain.run_after("after_search", ctx)
            return ctx.results
        except Exception as exc:
            self._chain.run_on_error(ctx, exc)
            raise

    def search_with_collector(self, query: Any, collector: Any) -> Any:
        ctx = MiddlewareContext("search_with_collector")
        ctx.query = str(query)
        ctx.collector = collector
        ctx = self._chain.run_before("before_search", ctx)
        try:
            results = self._searcher.search_with_collector(query, collector)
            ctx.results = results
            ctx = self._chain.run_after("after_search", ctx)
            return ctx.results
        except Exception as exc:
            self._chain.run_on_error(ctx, exc)
            raise

    def find(self, *args, **kwargs) -> Any:
        ctx = MiddlewareContext("find")
        ctx.query = str(args[0]) if args else ""
        ctx = self._chain.run_before("before_search", ctx)
        try:
            results = self._searcher.find(*args, **kwargs)
            ctx.results = results
            ctx = self._chain.run_after("after_search", ctx)
            return ctx.results
        except Exception as exc:
            self._chain.run_on_error(ctx, exc)
            raise

    def close(self) -> None:
        self._searcher.close()

    def __enter__(self) -> MiddlewareSearcher:
        return self

    def __exit__(self, *args) -> None:
        self._searcher.close()


__all__ = ["MiddlewareWriter", "MiddlewareSearcher"]
