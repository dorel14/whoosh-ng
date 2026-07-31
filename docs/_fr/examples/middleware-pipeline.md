---
title: "Pipeline de middleware"
nav_order: 245
lang: fr
---

# Pipeline de middleware

Le pipeline de middleware enveloppe les opérations avec des préoccupations transversales : nouvelle tentative, journalisation, etc.

## Architecture

```python
from whoosh_modern.middleware import Middleware, MiddlewarePipeline, RetryMiddleware, LoggingMiddleware

pipeline = MiddlewarePipeline(
    RetryMiddleware(attempts=3, backoff="exponential"),
    LoggingMiddleware(),
)

result = pipeline.execute(my_operation)
```

## RetryMiddleware

```python
from whoosh_modern.middleware import RetryMiddleware

retry = RetryMiddleware(attempts=3, backoff="exponential")

@retry.wrap
def operation():
    return fetch_data()
```

Stratégies de backoff :
- `"exponential"` : 1s, 2s, 4s, 8s...
- `"linear"` : 1s, 2s, 3s, 4s...

## LoggingMiddleware

```python
from whoosh_modern.middleware import LoggingMiddleware
import logging

logger = logging.getLogger("benchmark")
logging_mw = LoggingMiddleware(logger=logger)

@logging_mw.wrap
def tracked():
    return fetch_data()
```