"""Tests for whoosh_modern middleware."""

import pytest

from whoosh_modern.middleware import (
    CacheMiddleware,
    LoggingMiddleware,
    MiddlewarePipeline,
    RetryMiddleware,
)


class TestRetryMiddleware:
    def test_succeeds_on_first_attempt(self):
        middleware = RetryMiddleware(attempts=3)
        result = middleware.wrap(lambda: "success")()
        assert result == "success"

    def test_retries_on_failure(self):
        attempts = [0]

        def flaky():
            attempts[0] += 1
            if attempts[0] < 3:
                raise RuntimeError("fail")
            return "success"

        middleware = RetryMiddleware(attempts=3, backoff="none")
        wrapped = middleware.wrap(flaky)
        assert wrapped() == "success"
        assert attempts[0] == 3

    def test_raises_after_max_attempts(self):
        middleware = RetryMiddleware(attempts=2, backoff="none")

        def always_fail():
            raise RuntimeError("fail")

        wrapped = middleware.wrap(always_fail)
        with pytest.raises(RuntimeError):
            wrapped()


class TestLoggingMiddleware:
    def test_logs_success(self, caplog):
        import logging

        middleware = LoggingMiddleware(level=logging.INFO)
        wrapped = middleware.wrap(lambda: "ok")
        with caplog.at_level(logging.INFO):
            result = wrapped()
        assert result == "ok"
        assert "completed" in caplog.text

    def test_logs_failure(self, caplog):
        import logging

        middleware = LoggingMiddleware(level=logging.ERROR)

        def failing():
            raise RuntimeError("boom")

        wrapped = middleware.wrap(failing)
        with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError):
            wrapped()
        assert "failed" in caplog.text


class TestCacheMiddleware:
    def test_caches_result(self):
        counter = [0]

        def operation():
            counter[0] += 1
            return 42

        middleware = CacheMiddleware()
        wrapped = middleware.wrap(operation)
        assert wrapped() == 42
        assert wrapped() == 42
        assert counter[0] == 1

    def test_different_args_different_cache_keys(self):
        counter = [0]

        def operation(x):
            counter[0] += 1
            return x * 2

        middleware = CacheMiddleware()
        wrapped = middleware.wrap(operation)
        assert wrapped(1) == 2
        assert wrapped(2) == 4
        assert counter[0] == 2

    def test_stats_track_hits_and_misses(self):
        middleware = CacheMiddleware()
        wrapped = middleware.wrap(lambda: "value")
        wrapped()
        wrapped()
        stats = middleware.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1

    def test_clear_resets_cache(self):
        middleware = CacheMiddleware()
        wrapped = middleware.wrap(lambda: "value")
        wrapped()
        middleware.clear()
        stats = middleware.stats
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["size"] == 0

    def test_maxsize_evicts_oldest(self):
        middleware = CacheMiddleware(maxsize=2)
        wrapped = middleware.wrap(lambda x: x)
        wrapped(1)
        wrapped(2)
        wrapped(3)
        stats = middleware.stats
        assert stats["size"] == 2


class TestMiddlewarePipeline:
    def test_empty_pipeline_returns_result(self):
        pipeline = MiddlewarePipeline()
        result = pipeline.execute(lambda: "ok")
        assert result == "ok"

    def test_chains_middlewares(self):
        middleware = RetryMiddleware(attempts=3, backoff="none")
        pipeline = MiddlewarePipeline(middleware)
        result = pipeline.execute(lambda: "chained")
        assert result == "chained"
