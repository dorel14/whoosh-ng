"""Benchmarks for middleware pipeline performance."""

from __future__ import annotations

import time
from typing import Any

import pytest

pytest.importorskip("pytest_benchmark")

from whoosh_modern.middleware import (
    LoggingMiddleware,
    Middleware,
    MiddlewarePipeline,
    RetryMiddleware,
)


class DummyOperation:
    """Dummy operation for benchmarking middleware."""

    __name__ = "DummyOperation"

    def __call__(self) -> dict[str, Any]:
        return {"result": "ok", "data": [1, 2, 3]}


class BenchmarkMiddlewarePipeline:
    """Benchmark suite for middleware pipeline performance."""

    def setup_method(self):
        self.pipeline = MiddlewarePipeline(
            RetryMiddleware(attempts=3, backoff="exponential"),
            LoggingMiddleware(),
        )
        self.operation = DummyOperation()

    def benchmark_pipeline_execution(self, benchmark):
        """Benchmark full pipeline execution."""

        def _execute():
            return self.pipeline.execute(self.operation)

        result = benchmark(_execute)
        assert result is not None

    def benchmark_retry_middleware(self, benchmark):
        """Benchmark retry middleware with no failures."""
        retry = RetryMiddleware(attempts=3, backoff="exponential")

        @retry.wrap
        def _success():
            return {"status": "ok"}

        def _execute():
            return _success()

        result = benchmark(_execute)
        assert result["status"] == "ok"

    def benchmark_retry_with_failures(self, benchmark):
        """Benchmark retry middleware with intermittent failures."""
        retry = RetryMiddleware(attempts=3, backoff="exponential")
        attempt = 0

        @retry.wrap
        def _flaky():
            nonlocal attempt
            attempt += 1
            if attempt < 3:
                raise ConnectionError("Simulated failure")
            return {"status": "ok"}

        def _execute():
            nonlocal attempt
            attempt = 0
            return _flaky()

        result = benchmark(_execute)
        assert result["status"] == "ok"

    def benchmark_logging_middleware(self, benchmark):
        """Benchmark logging middleware overhead."""
        import logging

        logging_mw = LoggingMiddleware(logger=logging.getLogger("benchmark"))

        wrapped = logging_mw.wrap(self.operation)

        def _execute():
            return wrapped()

        result = benchmark(_execute)
        assert result is not None

    def benchmark_empty_pipeline(self, benchmark):
        """Benchmark pipeline with no middleware."""
        pipeline = MiddlewarePipeline()

        def _execute():
            return pipeline.execute(self.operation)

        result = benchmark(_execute)
        assert result is not None

    def benchmark_single_middleware(self, benchmark):
        """Benchmark pipeline with single middleware."""
        pipeline = MiddlewarePipeline(RetryMiddleware(attempts=1))

        def _execute():
            return pipeline.execute(self.operation)

        result = benchmark(_execute)
        assert result is not None

    def benchmark_many_middlewares(self, benchmark):
        """Benchmark pipeline with many middlewares."""
        pipeline = MiddlewarePipeline(
            RetryMiddleware(attempts=2),
            LoggingMiddleware(),
            RetryMiddleware(attempts=1),
            LoggingMiddleware(),
        )

        def _execute():
            return pipeline.execute(self.operation)

        result = benchmark(_execute)
        assert result is not None

    def benchmark_middleware_ordering_a(self, benchmark):
        """Benchmark pipeline with retry then logging."""
        pipeline = MiddlewarePipeline(
            RetryMiddleware(attempts=2),
            LoggingMiddleware(),
        )

        def _execute():
            return pipeline.execute(self.operation)

        benchmark(_execute)

    def benchmark_middleware_ordering_b(self, benchmark):
        """Benchmark pipeline with logging then retry."""
        pipeline = MiddlewarePipeline(
            LoggingMiddleware(),
            RetryMiddleware(attempts=2),
        )

        def _execute():
            return pipeline.execute(self.operation)

        benchmark(_execute)


class BenchmarkMiddlewareEdgeCases:
    """Benchmark edge cases for middleware."""

    def benchmark_linear_backoff(self, benchmark):
        """Benchmark retry with linear backoff."""
        retry = RetryMiddleware(attempts=3, backoff="linear")

        @retry.wrap
        def _success():
            return {"status": "ok"}

        def _execute():
            return _success()

        result = benchmark(_execute)
        assert result["status"] == "ok"

    def benchmark_immediate_retry(self, benchmark):
        """Benchmark retry with zero attempts (no retry)."""
        retry = RetryMiddleware(attempts=1)

        @retry.wrap
        def _success():
            return {"status": "ok"}

        def _execute():
            return _success()

        result = benchmark(_execute)
        assert result["status"] == "ok"

    def benchmark_custom_backoff(self, benchmark):
        """Benchmark retry with custom backoff."""
        retry = RetryMiddleware(attempts=2, backoff="exponential")

        @retry.wrap
        def _success():
            return {"status": "ok"}

        def _execute():
            return _success()

        result = benchmark(_execute)
        assert result["status"] == "ok"
