---
title: "Query API"
nav_order: 5
parent: "API Reference"
---

# Query API

Build and execute queries programmatically.

## QueryParser

```python
class whoosh.qparser.QueryParser(
    fieldname: str,
    schema: Schema,
    group=AndGroup,
    **kwargs
)
```

Convert a query string into a Query object.

### Methods

#### `parse()`

```python
query = qp.parse(querystring)
```

Parse a query string.

---

#### `tokenize()`

```python
tokens = qp.tokenize(querystring)
```

Tokenize a query string without parsing.

---

### MultifieldParser

```python
class whoosh.qparser.MultifieldParser(
    fieldnames: list,
    schema: Schema,
    fieldboosts: dict = None,
    group=OrGroup,
    **kwargs
)
```

Search multiple fields with different boosts.

**Example:**
```python
from whoosh.qparser import MultifieldParser

qp = MultifieldParser(
    ["title", "content"],
    schema,
    fieldboosts={"title": 2.0}
)
```

## Query Classes

All queries inherit from `Query`:

```python
class whoosh.query.Query
```

### Methods

#### `matcher()`

```python
matcher = query.matcher(searcher, context=None)
```

Return a matcher for executing the query.

#### `__and__()`, `__or__()`, `__invert__()`

Combine queries with `&`, `|`, `-`.

### Leaf Queries

#### Term

```python
Term(fieldname: str, text: str, boost: float = 1.0)
```

Match a specific term.

---

#### Phrase

```python
Phrase(fieldname: str, words: list, boost: float = 1.0, slop: int = 1)
```

Match a phrase.

---

#### Prefix

```python
Prefix(fieldname: str, text: str, boost: float = 1.0)
```

Match terms starting with `text`.

---

#### Wildcard

```python
Wildcard(fieldname: str, text: str, boost: float = 1.0)
```

Match terms with `?` and `*` wildcards.

---

#### FuzzyTerm

```python
FuzzyTerm(
    fieldname: str,
    text: str,
    maxdist: int = 2,
    prefix: int = 0,
    boost: float = 1.0
)
```

Fuzzy match with edit distance.

---

#### Range

```python
NumericRange(
    fieldname: str,
    start: Any,
    end: Any,
    startexact: bool = False,
    endexact: bool = False,
    boost: float = 1.0
)
```

Numeric range query.

```python
DateRange(
    fieldname: str,
    start: datetime,
    end: datetime,
    startexact: bool = False,
    endexact: bool = False,
    boost: float = 1.0
)
```

Date range query.

---

#### Every

```python
Every(fieldname: str, boost: float = 1.0)
```

Match every document with any term in this field.

### Boolean Queries

#### And

```python
And(children: list, boost: float = 1.0)
```

All children must match.

---

#### Or

```python
Or(children: list, boost: float = 1.0)
```

Any child must match.

---

#### Not

```python
Not(query, exclude)
```

Match docs matching query but not exclude.

---

#### DisjunctionMax

```python
DisjunctionMax(
    children: list,
    tiebreak: float = 0.0,
    boost: float = 1.0
)
```

OR-like with scoring tiebreaker.

### Special Queries

#### Require

```python
Require(match, requires)
```

Match must have `match`, and at least one of `requires`.

---

#### AndMaybe

```python
AndMaybe(must, should)
```

Must match `must`, optionally boosting with `should`.

---

#### Boost

```python
Boost(q, factor)
```

Multiply score by factor.

---

#### ConstantScore

```python
ConstantScore(q, score=1.0)
```

Assign constant score.

## Query Operators

```python
q1 & q2      # And
q1 | q2      # Or
~q1          # Not
q1 ^ q2      # DisjunctionMax
```

## Plugins

```python
from whoosh.qparser import QueryParserPlugin

class RangePlugin(QueryParserPlugin):
    def __init__(self):
        pass

    def evaluate(self, env, signode):
        # Return a query node
        return query.Range(signode.fieldname, ...)
```

## Exceptions

```python
class whoosh.qparser.QueryParserError(Exception)
```

Raised on parse errors.
