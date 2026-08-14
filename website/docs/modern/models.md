---
title: "Models"
sidebar_position: 45
---

# Models

Whoosh-NG can automatically map Python models to Whoosh `Schema` fields using
`ModelIndex` and `TypeMapper`. This covers dataclasses, Pydantic models,
SQLAlchemy models, SQLModel, msgspec, and plain annotated classes.

> **Module:** `whoosh_modern.models`
> **Version:** 3.0.0

## ModelIndex

`ModelIndex` inspects a Python model's type annotations and builds a Whoosh
`Schema` automatically.

```python
from dataclasses import dataclass
from whoosh_modern.models import ModelIndex

@dataclass
class Book:
    title: str
    count: int
    tag: str | None = None

idx = ModelIndex(Book)
schema = idx.schema
```

### Supported model types

| Model type | Detection |
|------------|-----------|
| Dataclass | `dataclasses.is_dataclass()` |
| Pydantic / HasFields | `isinstance(model, HasFields)` |
| SQLAlchemy | `hasattr(model, "__mapper__")` |
| Plain class | `inspect.get_annotations()` |

### Auto type mapping

| Python type | Whoosh field |
|-------------|--------------|
| `str` | `TEXT` |
| `int` / `float` | `NUMERIC` |
| `bool` | `BOOLEAN` |
| `datetime` / `date` | `DATETIME` |
| `Decimal` | `NUMERIC(int, decimal_places=2)` |
| `Enum` | `KEYWORD` |
| `bytes` | `KEYWORD` (hex-encoded) |
| `list[str]` | `KEYWORD` |
| `Optional[T]` | mapped type or `STORED` |

### ID field detection

`ModelIndex` auto-detects the ID field in this order:
1. Explicit `SearchOptions(id=True)`
2. Field named `id`, `ID`, or `_id`
3. First `str` field

### Converting instances to documents

```python
doc = idx.to_whoosh_document(book_instance)
# {"title": "Whoosh-NG", "count": 42, "tag": "search"}
```

## SearchOptions and SearchField

Use `SearchField` and `SearchOptions` to override auto-mapped defaults:

```python
from whoosh_modern.models import SearchField, SearchOptions

class Book:
    title: str = SearchField(fulltext=True, stored=True, analyzer="Simple")
    count: int = SearchField(sortable=True)
    tags: list[str] = SearchField(multi=True)
```

Or with `Annotated`:

```python
from typing import Annotated
from whoosh_modern.models import SearchField

class Book:
    title: Annotated[str, SearchField(fulltext=True, stored=True)]
```

## TypeMapper

`TypeMapper` is the central registry mapping Python types, runtime values,
and dtype names to Whoosh field types.

```python
from whoosh_modern.models import TypeMapper, SearchOptions

# Map a Python type
field = TypeMapper.map(str, SearchOptions(stored=True))

# Map an annotation (unwraps Optional and Annotated)
field = TypeMapper.map_annotation(int | None)

# Map a runtime value
field = TypeMapper.map_value(42)

# Map a dtype name (pandas, polars, SQL, etc.)
field = TypeMapper.map_dtype("int64")
```

### Registering custom mappings

```python
TypeMapper.register(MyType, lambda opt: TEXT(stored=opt.stored))
```

### Type suggestion

`TypeMapper.suggest_type(current, usage)` recommends a more specific Whoosh
field type for a `TEXT` field based on usage statistics:

```python
suggestion = TypeMapper.suggest_type("TEXT", {
    "doc_count": 1000,
    "unique_values": 950,
    "is_id": True,
    "is_bool": False,
    "is_datetime": False,
})
# "ID" or "KEYWORD" or None
```

## See Also

- [Schema](/core/schema) — Core Whoosh schema concepts
- [Auto-indexing](/modern/auto-indexing) — Schema discovery from data sources
- [Configuration Engine](/modern/configuration-engine) — Typed configuration surface
