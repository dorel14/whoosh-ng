---
color_scheme: dark
title: "Query Language"
nav_order: 25
parent: "Guides"
---

# Query Language

Whoosh-NG provides a powerful query language similar to Lucene's, as well as a programmatic query API.

## QueryParser

The `QueryParser` converts a query string into a query tree:

```python
from whoosh.qparser import QueryParser

# Parse a query for a specific field
qp = QueryParser("content", schema)
query = qp.parse("hello world")
```

## Query Syntax

### Basic Terms

```
hello                    # Single term
hello world              # Multiple terms (default AND)
hello OR world           # Explicit OR
"hello world"            # Phrase
```

### Field-Specific

```
title:python             # Search only in title field
title:"Python Tutorial"  # Phrase in specific field
```

### Boolean Operators

```
python AND whoosh
python OR whoosh
python AND NOT java
python AND (whoosh OR lucene)
```

### Prefix and Wildcard

```
pyth*                    # Prefix query
pyth?n                   # Single character wildcard
```

### Range Queries

```
date:[2020 TO 2025]
price:[10 TO 50]
rating:[4.0 TO *]        # Open-ended range
```

### Fuzzy Search

```
python~2                 # Edit distance <= 2
lucene~1                 # Approximate match
```

### Proximity Search

```
"hello world"~5          # Within 5 terms
```

### Boosting

```
python^2.0 whoosh        # Boost python by 2x
(title:python)^3 content:python  # Boost title matches
```

## Query Classes

You can build queries programmatically:

```python
from whoosh.query import *

# Simple term
q = Term("content", "python")

# Multiple terms (AND)
q = And([Term("content", "python"), Term("content", "whoosh")])

# Multiple terms (OR)
q = Or([Term("content", "python"), Term("content", "lucene")])

# Phrase
q = Phrase("content", ["hello", "world"])

# Range
q = NumericRange("price", 10, 50)
q = DateRange("date", datetime(2020,1,1), datetime(2025,1,1))

# Prefix
q = Prefix("content", "pyth")

# Wildcard
q = Wildcard("content", "pyth?n")

# Fuzzy
q = FuzzyTerm("content", "python", maxdist=2)

# Boost
q = Boost(Term("title", "python"), 2.0) & Term("content", "python")
```

## QueryParser Plugins

Extend query parsing with plugins:

```python
from whoosh.qparser import QueryParserPlugin

class MyPlugin(QueryParserPlugin):
    def __init__(self):
        pass

    def evaluate(self, env, signode):
        # Custom evaluation logic
        return Term("custom_field", signode.content)
```

## Multifield Search

Search multiple fields with different boosts:

```python
from whoosh.qparser import MultifieldParser

qp = MultifieldParser(
    ["title", "content", "tags"],
    schema,
    fieldboosts={"title": 2.0, "tags": 1.5}
)
q = qp.parse("python search")
```

## Default Operator

```python
from whoosh.qparser import QueryParser, OrGroup

# Default AND
qp = QueryParser("content", schema)

# Default OR
qp = QueryParser("content", schema, group=OrGroup)
```

## Escaping Special Characters

```
title\:python              # Literal colon
path\:\/\/example          # Escape special chars
```

## Regex Queries

```
content:/p[ya]thon/        # Regex match
```

## Advanced: Custom Queries

```python
from whoosh.query import Query

class CustomQuery(Query):
    def __init__(self, fieldname, text):
        self.fieldname = fieldname
        self.text = text

    def __repr__(self):
        return f"CustomQuery({self.fieldname!r}, {self.text!r})"

    def __hash__(self):
        return hash((self.fieldname, self.text))

    def __eq__(self, other):
        return (
            isinstance(other, CustomQuery)
            and self.fieldname == other.fieldname
            and self.text == other.text
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def matcher(self, searcher, context=None):
        # Return a custom matcher
        return CustomMatcher(searcher, self)
```
