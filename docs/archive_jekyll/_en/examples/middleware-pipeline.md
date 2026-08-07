---
title: "Middleware Pipeline"
nav_order: 251
---

# Middleware Pipeline

The middleware pipeline wraps operations with cross-cutting concerns: retry, logging, etc.

## Architecture

```python
from whoosh_modern.middleware import Middleware, MiddlewarePipeline, RetryMiddleware, LoggingMiddleware

# Chain middlewares
pipeline = MiddlewarePipeline(
    RetryMiddleware(attempts=3, backoff="exponential"),
    LoggingMiddleware(),
)

# Execute an operation through the chain
result = pipeline.execute(my_operation)
```

## RetryMiddleware

```python
from whoosh_modern.middleware import RetryMiddleware

retry = RetryMiddleware(attempts=3, backoff="exponential")

def flaky_operation():
    # Will retry up to 3 times on exception
    return fetch_data()

wrapped_op = retry.wrap(flaky_operation)
result = wrapped_op()
```

Backoff strategies:
- `"exponential"`: 1s, 2s, 4s, 8s...
- `"linear"`: 1s, 2s, 3s, 4s...

## LoggingMiddleware

```python
from whoosh_modern.middleware import LoggingMiddleware
import logging

logger = logging.getLogger("benchmark")
logging_mw = LoggingMiddleware(logger=logger, level=logging.INFO)

tracked_op = logging_mw.wrap(lambda: fetch_data())
result = tracked_op()
# Logs: "Operation wrapped completed in 0.123s"
# On error: "Operation wrapped failed after 0.123s: <error>"
```

## CacheMiddleware

```python
from whoosh_modern.middleware import CacheMiddleware

cache = CacheMiddleware(maxsize=128)

cached_op = cache.wrap(expensive_query)
result1 = cached_op(args)  # cache miss
result2 = cached_op(args)  # cache hit

print(cache.stats)  # {"hits": 1, "misses": 1, "size": 1}
cache.clear()
```

## Custom Middleware

```python
from whoosh_modern.middleware import Middleware

class TimingMiddleware(Middleware):
    def __init__(self):
        self.timings = []

    def wrap(self, operation):
        def wrapped(*args, **kwargs):
            start = time.time()
            try:
                result = operation(*args, **kwargs)
                self.timings.append(time.time() - start)
                return result
            except Exception:
                raise
        return wrapped
```
