import pytest

from whoosh.middleware.base import (
    CacheMiddleware,
    CompressionMiddleware,
    EncryptionMiddleware,
    MetricsMiddleware,
    Middleware,
)
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.context import MiddlewareContext
from whoosh.middleware.exceptions import StopOperation


class TestMiddlewareContext:
    def test_context_initialization(self):
        ctx = MiddlewareContext("index")
        assert ctx.operation == "index"
        assert ctx.document is None
        assert ctx.query == ""
        assert ctx.labels == {}
        assert ctx.metadata == {}

    def test_context_copy(self):
        ctx = MiddlewareContext("search")
        ctx.index = "test_index"
        ctx.query = "test query"
        ctx.labels["key"] = "value"
        copy = ctx.copy()
        assert copy.operation == "search"
        assert copy.index == "test_index"
        assert copy.query == "test query"
        assert copy.labels == {"key": "value"}


class TestMiddlewareBase:
    def test_middleware_context_passing(self):
        middleware = Middleware()
        ctx = MiddlewareContext("index")
        result = middleware.before_index(ctx)
        assert result is ctx

    def test_middleware_before_index_returns_context(self):
        ctx = MiddlewareContext("index")
        ctx.document = {"title": "test"}
        middleware = Middleware()
        result = middleware.before_index(ctx)
        assert result.document == {"title": "test"}


class TestCompressionMiddleware:
    def test_marks_document_for_compression(self):
        middleware = CompressionMiddleware()
        ctx = MiddlewareContext("index")
        ctx.document = {"title": "test"}
        result = middleware.before_index(ctx)
        assert result.document.get("_compressed") is True


class TestEncryptionMiddleware:
    def test_marks_document_for_encryption(self):
        middleware = EncryptionMiddleware()
        ctx = MiddlewareContext("index")
        ctx.document = {"title": "secret"}
        result = middleware.before_index(ctx)
        assert result.document.get("_encrypted") is True


class TestMetricsMiddleware:
    def test_counts_indexed_documents(self):
        middleware = MetricsMiddleware()
        ctx = MiddlewareContext("index")
        middleware.after_index(ctx)
        middleware.after_index(ctx)
        assert middleware.get_metrics()["documents_indexed"] == 2

    def test_counts_searches(self):
        middleware = MetricsMiddleware()
        ctx = MiddlewareContext("search")
        ctx.results = []
        middleware.after_search(ctx)
        middleware.after_search(ctx)
        assert middleware.get_metrics()["searches_executed"] == 2


class TestCacheMiddleware:
    def test_caches_search_results(self):
        middleware = CacheMiddleware()
        ctx = MiddlewareContext("search")
        ctx.query = "test"
        ctx.results = [{"id": 1}]
        middleware.after_search(ctx)
        assert middleware.get_cached("test") == [{"id": 1}]

    def test_sets_cache_explicitly(self):
        middleware = CacheMiddleware()
        middleware.set_cached("foo", [{"id": 2}])
        assert middleware.get_cached("foo") == [{"id": 2}]


class TestMiddlewareChain:
    def test_empty_chain_passes_context_through(self):
        chain = MiddlewareChain()
        ctx = MiddlewareContext("index")
        ctx.document = {"test": "data"}
        before = chain.run_before("before_index", ctx)
        after = chain.run_after("after_index", before)
        assert before is after

    def test_chain_executes_middleware_in_order(self):
        class BeforeMiddleware(Middleware):
            def before_index(self, ctx):
                ctx.labels["order"] = ctx.labels.get("order", []) + ["before"]
                return ctx

        class AfterMiddleware(Middleware):
            def after_index(self, ctx):
                ctx.labels["order"] = ctx.labels.get("order", []) + ["after"]
                return ctx

        chain = MiddlewareChain([BeforeMiddleware(), AfterMiddleware()])
        ctx = MiddlewareContext("index")
        ctx = chain.run_before("before_index", ctx)
        ctx = chain.run_after("after_index", ctx)
        assert ctx.labels["order"] == ["before", "after"]

    def test_stop_operation_can_be_raised(self):
        class StoppingMiddleware(Middleware):
            def before_index(self, ctx):
                raise StopOperation("blocked")

        chain = MiddlewareChain([StoppingMiddleware()])
        ctx = MiddlewareContext("index")
        with pytest.raises(StopOperation):
            chain.run_before("before_index", ctx)
