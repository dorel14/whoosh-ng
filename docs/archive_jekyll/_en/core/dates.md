---
title: "Dates and Numeric Ranges"
nav_order: 29
permalink: /en/guides/dates/
---

# Dates and Numeric Ranges

This guide covers working with `DATETIME` and `NUMERIC` fields, including
range queries, range faceting, and date math.

## DATETIME Fields

`DATETIME` fields store Python `datetime` objects and can be queried with
range queries.

```python
from datetime import datetime
from whoosh import fields, index

schema = fields.Schema(
    title=fields.TEXT(stored=True),
    published_date=fields.DATETIME(stored=True, sortable=True),
)
```

### Indexing Dates

```python
ix = index.create_in("indexdir", schema)
with ix.writer() as w:
    w.add_document(
        title="Article 1",
        published_date=datetime(2024, 6, 15, 14, 30),
    )
```

### Date Range Queries

Use `Range` or `QueryParser` syntax:

```python
from whoosh.qparser import QueryParser
from whoosh.query import Range, Every

# Using QueryParser syntax
qp = QueryParser("published_date", schema=ix.schema)
q = qp.parse("[2024-01-01 TO 2024-12-31]")

# Using Range query directly
from datetime import datetime
q = Range(
    "published_date",
    datetime(2024, 1, 1),
    datetime(2024, 12, 31),
)

with ix.searcher() as searcher:
    results = searcher.search(q)
```

### Sorting by Date

```python
from whoosh.sorting import FieldFacet

# Sort by date, most recent first
results = searcher.search(
    query,
    sortedby=FieldFacet("published_date", reverse=True),
)
```

## NUMERIC Fields

`NUMERIC` fields store integers and floating-point numbers.

```python
schema = fields.Schema(
    title=fields.TEXT(stored=True),
    price=fields.NUMERIC(int, stored=True, sortable=True),
    rating=fields.NUMERIC(float, stored=True),
)
```

### Numeric Range Queries

```python
from whoosh.query import NumericRange

q = NumericRange("price", 100, 500)

# Or with QueryParser
qp = QueryParser("price", schema=ix.schema)
q = qp.parse("[100 TO 500]")
```

### Numeric Faceting

Group results into numeric ranges using `RangeFacet`:

```python
from whoosh.sorting import RangeFacet

price_ranges = RangeFacet("price", 0, 1000, 100)
results = searcher.search(query, groupedby=price_ranges)

for groupname, docnums in results.groups("price").items():
    print(f"Price ${groupname}: {len(docnums)} results")
```

## Date Faceting

Group results by date intervals using `DateRangeFacet`:

```python
from datetime import datetime
from whoosh.sorting import DateRangeFacet

start = datetime(2020, 1, 1)
end = datetime(2026, 1, 1)
date_facet = DateRangeFacet(
    "published_date",
    start,
    end,
    relativedelta(years=1),  # Requires: from dateutil.relativedelta import relativedelta
)
results = searcher.search(query, groupedby=date_facet)

for year_range, docnums in results.groups("published_date").items():
    print(f"Year {year_range}: {len(docnums)} results")
```

## Sorting and Filtering by Numbers

### Sorting

```python
from whoosh.sorting import FieldFacet

# Sort by price ascending
results = searcher.search(query, sortedby=FieldFacet("price"))
```

### Filtering

```python
from whoosh.query import NumericRange

# Only results with price >= 50 and price < 200
filter_q = NumericRange("price", 50, 200)
results = searcher.search(query, filter=filter_q)
```

## Making Date/Numeric Fields Sortable

When defining a schema, set `sortable=True` on `NUMERIC` or `DATETIME` fields
to enable sorting by that field:

```python
schema = fields.Schema(
    title=fields.TEXT(stored=True),
    price=fields.NUMERIC(int, sortable=True),
    date=fields.DATETIME(sortable=True),
)
```

If you forgot to set `sortable=True`, you can add it after indexing:

```python
from whoosh import index, sorting

ix = index.open_dir("indexdir")
with ix.writer() as w:
    sorting.add_sortable(w, "price", sorting.FieldFacet("price"))
```
