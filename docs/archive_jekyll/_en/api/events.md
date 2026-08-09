---
title: "Event Bus & Hooks API"
nav_order: 160
---

# Event Bus & Hooks API

Loose coupling through events and lightweight hooks.

## Event Bus

```python
class whoosh.event_bus.EventBus
```

Publish/subscribe event system supporting both synchronous and asynchronous
listeners. The module-level singleton `event_bus` is available for use:

```python
from whoosh.event_bus import event_bus
```

### Methods

#### `subscribe()`

```python
@event_bus.subscribe(DocumentIndexed)
async def handler(event: DocumentIndexed):
    print(f"Indexed document: {event.document_id}")

# Or without decorator
event_bus.subscribe(DocumentIndexed)(handler)
```

Register a handler function (synchronous or async) for a specific event type.
The decorator takes the event class as an argument. Returns the handler
unchanged so it can be used normally.

---

#### `publish()`

```python
from whoosh.event_bus import event_bus, DocumentIndexed

event_bus.publish(DocumentIndexed(document_id="doc123"))
```

Publish an event to all subscribers. If listeners are async coroutines and no
event loop is running, they are executed via `asyncio.run()`. If an event
loop is running, tasks are scheduled on it. Exceptions in listeners are
swallowed.

---

#### `clear()`

```python
event_bus.clear()
```

Remove all subscribers.

---

## Events

Events are immutable dataclasses.

### `Event`

```python
@dataclass(frozen=True)
class Event:
    pass
```

Base class for all events.

---

### `DocumentIndexed`

```python
@dataclass(frozen=True)
class DocumentIndexed(Event):
    document_id: str
```

Published when a document is indexed. Contains the document ID.

---

### `SearchExecuted`

```python
@dataclass(frozen=True)
class SearchExecuted(Event):
    query: str
```

Published after a search is executed. Contains the query string.

---

## Hooks

Hook system for cross-cutting concerns. Hooks are registered globally using a
module-level registry.

### `hookimpl`

```python
from whoosh.hooks import hookimpl

@hookimpl
def before_search(context):
    context.query = optimize_query(context.query)
    return context
```

Decorator that marks a function as a hook implementation. Returns a `HookImpl`
wrapper.

### `register_hook()`

```python
from whoosh.hooks import register_hook, hookimpl

@hookimpl
def before_search(context):
    ...

register_hook("before_search", before_search)
```

Register a `HookImpl` under a named hook. Multiple hooks can be registered
per name; they are called in registration order.

### `call_hook()`

```python
from whoosh.hooks import call_hook

results = await call_hook("before_search", context)
```

Async function that calls all hooks registered under the given name. Returns
a list of results from each hook's execution. Exceptions in individual hooks
are logged but do not stop execution.

---
## Example: Event Bus

```python
from whoosh.event_bus import event_bus, DocumentIndexed, SearchExecuted

@event_bus.subscribe(DocumentIndexed)
async def on_document_indexed(event: DocumentIndexed):
    print(f"Document indexed: {event.document_id}")

@event_bus.subscribe(SearchExecuted)
async def on_search_executed(event: SearchExecuted):
    print(f"Search executed: {event.query}")

# Publish events
event_bus.publish(DocumentIndexed(document_id="doc123"))
event_bus.publish(SearchExecuted(query="hello world"))
```

## Example: Hooks

```python
from whoosh.hooks import hookimpl, register_hook, call_hook
import asyncio

@hookimpl
def before_search(context):
    print(f"Searching for: {context['query']}")
    return context

register_hook("before_search", before_search)

# Call hooks
context = {"query": "hello"}
results = asyncio.run(call_hook("before_search", context))
```
