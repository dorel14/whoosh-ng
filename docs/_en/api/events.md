---
color_scheme: dark
title: "Event Bus & Hooks API"
nav_order: 8
parent: "API Reference"
---

# Event Bus & Hooks API

Loose coupling through events and lightweight hooks.

## Event Bus

```python
class whoosh.event_bus.EventBus
```

Publish/subscribe event system.

### Methods

#### `subscribe()`

```python
@bus.subscribe
def handler(event):
    ...

bus.subscribe(handler)
```

Subscribe a handler function.

---

#### `publish()`

```python
bus.publish(event)
```

Publish an event to all subscribers.

---

#### `clear()`

```python
bus.clear()
```

Remove all subscribers.

---

### Events

Events are dataclasses or namedtuples.

#### DocumentIndexed

```python
@dataclass
class DocumentIndexed:
    docnum: int
    document: dict
```

---

#### SearchExecuted

```python
@dataclass
class SearchExecuted:
    query: str
    results: Results
    duration: float
```

---

#### IndexingStarted

```python
@dataclass
class IndexingStarted:
    pass
```

---

#### IndexingCompleted

```python
@dataclass
class IndexingCompleted:
    pass
```

---

#### SearchStarted

```python
@dataclass
class SearchStarted:
    query: str
```

---

#### SearchCompleted

```python
@dataclass
class SearchCompleted:
    query: str
    duration: float
    result_count: int
```

---

## Hooks

```python
class whoosh.hooks.HookImpl
```

Decorator to mark a function as a hook implementation.

### Functions

#### `register_hook()`

```python
def register_hook(
    name: str,
    impl: HookImpl,
    registry: dict = None
) -> dict
```

Register a hook.

---

#### `call_hook()`

```python
results = call_hook(
    name: str,
    *args,
    registry: dict = None,
    **kwargs
)
```

Call all registered hooks.

---

## Example: Event Bus

```python
from whoosh.event_bus import EventBus, DocumentIndexed

bus = EventBus()

@bus.subscribe
def on_indexed(event: DocumentIndexed):
    print(f"Indexed doc {event.docnum}")

# Publish from middleware
bus.publish(DocumentIndexed(docnum=0, document={"title": "Hello"}))
```

## Example: Hooks

```python
from whoosh.hooks import hookimpl, register_hook, call_hook

@hookimpl
def before_search(context):
    context.query = optimize_query(context.query)
    return context

registry = {}
registry = register_hook("before_search", before_search, registry)

# Call all hooks
results = call_hook("before_search", context, registry=registry)
```
