"""Tests for middleware components."""

from collections.abc import Callable
from unittest.mock import MagicMock

import pytest

from whoosh_modern.middleware import (
    LoggingMiddleware,
    Middleware,
    MiddlewarePipeline,
    RetryMiddleware,
)


class DummyOperation:
    """Dummy operation for middleware testing."""

    __name__ = "DummyOperation"

    def __call__(self):
        return {"result": "ok", "data": [1, 2, 3]}


class TestRetryMiddleware:
    def test_retry_on_success(self):
        retry = RetryMiddleware(attempts=3, backoff="exponential")

        @retry.wrap
        def _success():
            return {"status": "ok"}

        result = _success()
        assert result["status"] == "ok"

    def test_retry_on_failure_exhausts_attempts(self):
        retry = RetryMiddleware(attempts=2, backoff="exponential")
        attempt = 0

        @retry.wrap
        def _flaky():
            nonlocal attempt
            attempt += 1
            raise ConnectionError("Simulated failure")

        with pytest.raises(ConnectionError):
            _flaky()
        assert attempt == 2

    def test_retry_retries_successfully(self):
        retry = RetryMiddleware(attempts=3, backoff="exponential")
        attempt = 0

        @retry.wrap
        def _flaky():
            nonlocal attempt
            attempt += 1
            if attempt < 2:
                raise ConnectionError("Simulated failure")
            return {"status": "ok"}

        result = _flaky()
        assert result["status"] == "ok"
        assert attempt == 2

    def test_exponential_backoff(self):
        retry = RetryMiddleware(attempts=3, backoff="exponential", jitter=False)
        delay0 = retry._calculate_delay(0)
        delay1 = retry._calculate_delay(1)
        delay2 = retry._calculate_delay(2)
        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 4.0

    def test_linear_backoff(self):
        retry = RetryMiddleware(attempts=3, backoff="linear", jitter=False)
        delay0 = retry._calculate_delay(0)
        delay1 = retry._calculate_delay(1)
        delay2 = retry._calculate_delay(2)
        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 3.0

    def test_backoff_with_jitter(self):
        retry = RetryMiddleware(attempts=3, backoff="exponential", jitter=True)
        delays = [retry._calculate_delay(1) for _ in range(10)]
        assert all(d > 0 for d in delays)
        assert all(d != delays[0] for d in delays[1:])

    def test_no_jitter(self):
        retry = RetryMiddleware(attempts=3, backoff="exponential", jitter=False)
        delay = retry._calculate_delay(1)
        assert delay == 2.0


class TestLoggingMiddleware:
    def test_logs_success(self):
        mock_logger = MagicMock()
        mw = LoggingMiddleware(logger=mock_logger)

        @mw.wrap
        def _op():
            return "result"

        result = _op()
        assert result == "result"
        mock_logger.log.assert_called()

    def test_logs_error(self):
        mock_logger = MagicMock()
        mw = LoggingMiddleware(logger=mock_logger)

        @mw.wrap
        def _fail():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            _fail()
        mock_logger.error.assert_called()

    def test_custom_logger(self):
        import logging

        custom_logger = logging.getLogger("custom_test")
        mw = LoggingMiddleware(logger=custom_logger)
        assert mw._logger is custom_logger


class TestMiddlewarePipeline:
    def test_empty_pipeline(self):
        pipeline = MiddlewarePipeline()

        def _op():
            return "result"

        result = pipeline.execute(_op)
        assert result == "result"

    def test_single_middleware(self):
        pipeline = MiddlewarePipeline(RetryMiddleware(attempts=1))

        def _op():
            return "result"

        result = pipeline.execute(_op)
        assert result == "result"

    def test_multiple_middlewares(self):
        pipeline = MiddlewarePipeline(
            RetryMiddleware(attempts=2),
            LoggingMiddleware(),
        )

        def _op():
            return "result"

        result = pipeline.execute(_op)
        assert result == "result"

    def test_pipeline_with_retry_then_logging(self):
        pipeline = MiddlewarePipeline(
            RetryMiddleware(attempts=2),
            LoggingMiddleware(),
        )

        attempt = 0

        def _flaky():
            nonlocal attempt
            attempt += 1
            if attempt < 2:
                raise ConnectionError("fail")
            return "ok"

        result = pipeline.execute(_flaky)
        assert result == "ok"


class TestMiddlewareBase:
    def test_middleware_is_abstract(self):
        with pytest.raises(TypeError):
            Middleware()  # type: ignore[abstract]

    def test_middleware_wrap_abstract(self):
        class ConcreteMiddleware(Middleware):
            def wrap(self, operation: Callable) -> Callable:
                return operation

        mw = ConcreteMiddleware()

        def _op():
            return "result"

        wrapped = mw.wrap(_op)
        assert wrapped() == "result"
