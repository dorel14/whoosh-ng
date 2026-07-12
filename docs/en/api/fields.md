---
color_scheme: dark
title: "Fields"
nav_order: 2
parent: "API Reference"
---

# Fields API

Define the structure of your index with field types.

## Schema

```python
class whoosh.fields.Schema
```

The `Schema` class defines the fields available in an index.

### Constructor

```python
schema = Schema(
    title=TEXT(stored=True),
    content=TEXT,
    path=ID(stored=True, unique=True),
    tags=KEYWORD(lowercase=True),
    rating=NUMERIC(float, stored=True),
    published=DATETIME(stored=True),
    active=BOOLEAN
)
```

### Methods

#### `add()`

```python
schema.add(
    fieldname: str,
    fieldtype,
    glob: bool = False,
    **kwargs
)
```

Add a field to the schema. If `glob=True`, the fieldname is treated as a glob pattern.

#### `remove()`

```python
schema.remove(fieldname: str, **kwargs)
```

Remove a field from the schema.

#### `items()`

```python
for name, field in schema.items():
    print(name, field)
```

Return a list of (fieldname, field object) pairs.

#### `names()`

```python
names = schema.names()
```

Return a list of field names.

## FieldType Base Class

```python
class whoosh.fields.FieldType
```

Base class for all field types.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `format` | `Format` | Defines how the field is indexed |
| `vector` | `Format` or None | Optional per-document vector format |
| `scorable` | `bool` | Whether field length is stored (for BM25F) |
| `stored` | `bool` | Whether field value is stored in index |
| `unique` | `bool` | Whether field uniquely identifies documents |

### Methods

#### `index()`

Convert a value into indexed items.

#### `indexable()`

Check if the value can be indexed.

#### `spelling_fieldname()`

Return the field name used for spelling data.

#### `spellable_words()`

Generate spellable words from a value.

## Built-in Field Types

### TEXT

```python
whoosh.fields.TEXT(
    stored: bool = False,
    unique: bool = False,
    phrase: bool = True,
    analyzer: Analyzer = None,
    field_boost: float = 1.0,
    **kwargs
)
```

Full-text field with tokenization and optional phrase search.

**Example:**
```python
title = TEXT(stored=True)
body = TEXT(analyzer=StemmingAnalyzer(), phrase=False)
```

---

### ID

```python
whoosh.fields.ID(
    stored: bool = False,
    unique: bool = False,
    field_boost: float = 1.0,
    **kwargs
)
```

Untokenized identifier field. Stores the entire value as a single term.

**Example:**
```python
path = ID(stored=True, unique=True)
slug = ID(stored=True)
```

---

### KEYWORD

```python
whoosh.fields.KEYWORD(
    stored: bool = False,
    lowercase: bool = False,
    commas: bool = False,
    scorable: bool = False,
    field_boost: float = 1.0,
    **kwargs
)
```

Space or comma-separated keywords. Phrase search is not supported.

**Example:**
```python
tags = KEYWORD(lowercase=True, commas=True, stored=True)
```

---

### STORED

```python
whoosh.fields.STORED(
    stored: bool = True,
    unique: bool = False,
    **kwargs
)
```

Stored-only field. Not indexed or searchable.

**Example:**
```python
icon = STORED()
description = STORED()
```

---

### NUMERIC

```python
whoosh.fields.NUMERIC(
    numtype: type = int,
    stored: bool = False,
    unique: bool = False,
    field_boost: float = 1.0,
    **kwargs
)
```

Numeric field for integers or floats.

**Example:**
```python
rating = NUMERIC(float, stored=True)
count = NUMERIC(int)
price = NUMERIC(float, stored=True, sortable=True)
```

---

### DATETIME

```python
whoosh.fields.DATETIME(
    stored: bool = False,
    unique: bool = False,
    field_boost: float = 1.0,
    **kwargs
)
```

Date/time field. Stores `datetime` objects.

**Example:**
```python
published = DATETIME(stored=True)
updated = DATETIME()
```

---

### BOOLEAN

```python
whoosh.fields.BOOLEAN(
    stored: bool = False,
    unique: bool = False,
    field_boost: float = 1.0,
    **kwargs
)
```

Boolean field. Searchable with `yes`, `no`, `true`, `false`, `1`, `0`, `t`, `f`.

**Example:**
```python
published = BOOLEAN(stored=True)
```

---

### NGRAM

```python
whoosh.fields.NGRAM(
    minsize: int = 2,
    maxsize: int = 5,
    stored: bool = False,
    field_boost: float = 1.0,
    **kwargs
)
```

Character n-gram field.

---

### NGRAMWORDS

```python
whoosh.fields.NGRAMWORDS(
    minsize: int = 2,
    maxsize: int = 5,
    stored: bool = False,
    field_boost: float = 1.0,
    **kwargs
)
```

Word-level n-gram field.

---

### VectorField

```python
whoosh.fields.VectorField(
    dimensions: int,
    metric: str = "cosine",
    provider: str = "numpy",
    stored: bool = False,
    **kwargs
)
```

Field for storing and searching vector embeddings.

**Args:**
- `dimensions (int)`: Embedding dimension (e.g., 384 for all-MiniLM-L6-v2).
- `metric (str)`: Similarity metric: `"cosine"`, `"euclidean"`, `"dot"`.
- `provider (str)`: Vector provider name from registry.

**Example:**
```python
embedding = VectorField(dimensions=384, metric="cosine", stored=True)
```

## SchemaBuilder

Fluent API for building schemas:

```python
from whoosh.fields import SchemaBuilder

schema = (
    SchemaBuilder()
    .field("title", TEXT(stored=True))
    .field("path", ID(stored=True, unique=True))
    .field("content", TEXT)
    .field("tags", KEYWORD(lowercase=True))
    .field("published", DATETIME(stored=True))
    .build()
)
```

## Constants

- `whoosh.fields.STORED`: Stored-only field type
- `whoosh.fields.TEXT`: Full-text field
- `whoosh.fields.ID`: Identifier field
- `whoosh.fields.KEYWORD`: Keyword field
- `whoosh.fields.NUMERIC`: Numeric field
- `whoosh.fields.DATETIME`: Date/time field
- `whoosh.fields.BOOLEAN`: Boolean field
