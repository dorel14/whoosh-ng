"""Observability middleware for Whoosh-NG.

Optional metrics collection with Prometheus exporter.
Requires prometheus-client to be installed.
"""

from whoosh.middleware.context import MiddlewareContext


class PrometheusMiddleware:
    """Middleware that exports metrics to Prometheus.

    Requires prometheus-client to be installed via extras.
    """

    def __init__(self) -> None:
        try:
            from prometheus_client import Counter, Histogram

            self._search_counter = Counter(
                "whoosh_searches_total", "Total number of searches executed"
            )
            self._index_counter = Counter(
                "whoosh_documents_indexed_total", "Total number of documents indexed"
            )
            self._search_duration = Histogram(
                "whoosh_search_duration_seconds", "Search execution time"
            )
        except ImportError as exc:
            raise ImportError(
                "PrometheusMiddleware requires prometheus-client. "
                "Install with: pip install whoosh-reloaded[metrics]"
            ) from exc

    def before_search(self, context: MiddlewareContext) -> MiddlewareContext:
        import time

        context.metadata["_start_time"] = time.time()
        return context

    def after_search(self, context: MiddlewareContext) -> MiddlewareContext:
        import time

        self._search_counter.inc()
        start = context.metadata.get("_start_time")
        if start:
            self._search_duration.observe(time.time() - start)
        return context

    def after_index(self, context: MiddlewareContext) -> MiddlewareContext:
        self._index_counter.inc()
        return context

    def on_commit(self, context: MiddlewareContext) -> None:
        pass

    def shutdown(self, context: MiddlewareContext) -> None:
        pass

    def startup(self, context: MiddlewareContext) -> None:
        pass


__all__ = ["PrometheusMiddleware"]