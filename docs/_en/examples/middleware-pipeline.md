---
title: "Middleware Pipeline"
nav_order: 245
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

@retry.wrap
def flaky_operation():
    # Will retry up to 3 times on exception
    return fetch_data()
```

Backoff strategies:
- `"exponential"`: 1s, 2s, 4s, 8s...
- `"linear"`: 1s, 2s, 3s, 4s...

## LoggingMiddleware

```python
from whoosh_modern.middleware import LoggingMiddleware
import logging

logger = logging.getLogger("benchmark")
logging_mw = LoggingMiddleware(logger=logger)

@logging_mw.wrap
def tracked_operation():
    return fetch_data()
# Logs: "Operation tracked_operation completed in 0.123s"
# On error: "Operation tracked_operation failed after 0.123s: <error>"
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
