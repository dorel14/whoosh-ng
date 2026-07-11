---
title: "Monitoring"
nav_order: 31
parent: "Guides"
---

# Monitoring

Whoosh-NG ships with hooks for observability and a Prometheus plugin for production use.

## Built-in Metrics

```python
from whoosh.middleware import MetricsMiddleware, MiddlewareChain
from whoosh.middleware.integration import apply_middleware_to_writer, apply_middleware_to_searcher

chain = MiddlewareChain([MetricsMiddleware()])
writer = apply_middleware_to_writer(ix.writer(), chain.middlewares)
searcher = apply_middleware_to_searcher(ix.searcher(), chain.middlewares)

metrics = chain.get_metrics()
print(metrics)
```

## Prometheus

```bash
pip install whoosh-ng[metrics]
```

| Metric | Type | Description |
|--------|------|-------------|
| `whoosh_documents_indexed_total` | Counter | Total documents indexed |
| `whoosh_searches_executed_total` | Counter | Total searches executed |
| `whoosh_indexing_duration_seconds` | Histogram | Indexing latency |
| `whoosh_search_duration_seconds` | Histogram | Search latency |
| `whoosh_index_size_bytes` | Gauge | Current index size |

## Best practices

1. Add `MetricsMiddleware` early in your base chain.
2. Expose `/metrics` in production.
3. Use `/health` for load balancer health checks.
4. Emit `DocumentIndexed` and `SearchExecuted` events.
