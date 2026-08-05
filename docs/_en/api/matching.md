---
title: "Matching API"
nav_order: 170
---

# Matching API

Classes and functions for iterating over and combining result sets during
searching. The matching module is a refactored package exposing the same
public API as the former monolithic module.

## Overview

When you search an index, Whoosh creates `Matcher` objects representing the
postings (document IDs and scores) produced by query objects. Matchers can
be combined (e.g., union, intersection) to build compound queries. The
matching module provides the core `Matcher` class hierarchy, utility
functions, and concrete implementations for various query types.

## Core Matcher Classes

### `Matcher`

```python
class whoosh.matching.Matcher
```

Abstract base class for all matchers. Concrete subclasses implement
`__init__()` and the `_set()` and `_maybe_values()` methods.

**Methods:**

#### `init = property(is_active)`

Property that returns whether the matcher is "active" (at top of segment
postings, not exhausted).

#### `init(view, docnum, score)`

Called when the matcher is initialized.

#### `set(matcher)`

Replaces this matcher with another one.

#### `copy()`

Returns a copy of this matcher.

#### `all_ids()`

Returns a list of docnums matched by this matcher.

#### `matches(matcher)`

Returns `True` if any of the current matches in `self` also match in
`matcher`.

#### `skip_to(docid)`

Advances the matcher to the first match at or after `docid`.

#### `skip_to_intersect(matcher)`

Moves this matcher to the earliest matching docnum that is also matched in
`matcher`.

#### `next()`

Advances the matcher to the next match.

#### `next_in_segment()`

Advances to the next match in the current segment.

#### `next_segment(matcher)`

Advances to the next segment in the context of `matcher`.

#### `is_active(in_segment=False)`

Returns `True` if this matcher has more matches to process.

#### `all_matching_segments()`

Generates `(segment_num, matcher)` pairs for all matching segments.

#### `doc()`

Returns the current document number of this matcher. May advance to next
document if not already on one.

#### `docnum()`

Returns the current docnum (segment-relative) of the matcher.

#### `score()`

Returns the current match's score.

#### `value()`

Returns the current match's value (e.g., the decoded stored value of the
term).

#### `supports()`

Returns `True` if `value()` is supported.

#### `value_matches()`

Returns the value at the current match.

#### `all_values()`

Returns a list of all values in this matcher.

#### `supports_lee()`

Returns `True` if the matcher uses lazy evaluation.

#### `lee`

Returns the current "lazy evaluation extension" value (for term vectors).

#### `spans()`

If the postings include positions, returns a list of `Position` objects for
the current match.

#### `spans()`

Returns the spans (positions) of the match in the current document.

#### `next_type()`

Returns the type of the next match.

#### `copy()`

Returns a shallow copy of this matcher.

### `Child`

```python
class whoosh.matching.Child
```

Mixin class for matchers that wrap other matchers.

### `FilterMixin`

```python
class whoosh.matching.FilterMixin
```

Mixin for matchers used as filters (boolean scoring, no relevance).

### `Custom`

```python
class whoosh.matching.Custom
```

Mixin for matchers that return a custom score from `score()` rather than 1.

### `Constant`

```python
class whoosh.matching.Constant
```

Mixin for matchers whose score is always the same value.

### `Coord`

```python
class whoosh.matching.Coord
```

Mixin for matchers that compute coordination factor (for phrase and other
queries that benefit from it).

## Concrete Matcher Classes

### `ListUnion`

```python
class whoosh.matching.ListUnion(matcher, items, maptype=None)
```

Base class for matchers that combine multiple matchers with a list of keys.

#### `filter`

```python
class whoosh.matching.filter
```

Decorator for creating filter matchers (boolean matchers with no relevance).

### `Union`

```python
class whoosh.matching.Union(matcher, items)
```

Base class for the `OR` operator.

### `Intersection`

```python
class whoosh.matching.Intersection(matcher, items)
```

The `AND` operator. A document matches only if it appears in all the child
matchers.

#### `IntersectionFilter`

```python
class whoosh.matching.IntersectionFilter(matcher, items)
```

A filter (no scoring) version of intersection.

### `And`

```python
class whoosh.matching.And(matcher, items)
```

Alias for `Intersection`.

### `Or`

```python
class whoosh.matching.Or(matcher, items)
```

Alias for `Union`.

### `Not`

```python
class whoosh.matching.Not(matcher, a, b)
```

The `NOT` operator. Matches all documents in `a` that are not in `b`.

### `Require`

```python
class whoosh.matching.Require(matcher, a, b)
```

Matches documents in `a` only if they also appear in `b`, but does not add
`b`'s score.

### `AndNot`

```python
class whoosh.matching.AndNot(matcher, a, b)
```

Matches documents in `a` that are not in `b`.

#### `AndMaybe`

```python
class whoosh.matching.AndMaybe(matcher, a, b)
```

Matches documents in `a`, adding `b`'s score if present.

### `BinaryUnion`

```python
class whoosh.matching.BinaryUnion(items)
```

Efficient intersection of exactly two matchers.

#### `BinaryUnion2`

```python
class whoosh.matching.BinaryUnion2
```

Optimized binary union for two items.

### `TreeMatcher`

```python
class whoosh.matching.TreeMatcher
```

A matcher that wraps a `Tree` object for combining results.

### `NestedParent`

```python
class whoosh.matching.NestedParent(parent, child, bools=False)
```

Matches parent documents that have at least one child document matched by
the child matcher. Used for nested document queries.

### `NestedChildren`

```python
class who which.matching.NestedChildren(parentmatch, child)
```

Matches child documents for a given parent document.

### `LengthMatcher`

```python
class whoosh.matching.LengthMatcher(child, q, polarity=False)
```

Matches documents based on field length (used by `Every` query).

### `Filter`

```python
class whoosh.matching.Filter(matcher)
```

Converts any matcher into a filter (no scoring).

### `AlwaysFilter`

```python
class whoosh.matching.AlwaysFilter
```

A filter that matches all documents.

### `NeverFilter`

```python
class whoosh.matching.NeverFilter
```

A filter that matches no documents.

### `PseudoMatcher`

```python
class whoosh.matching.PseudoMatcher
```

Base class for pseudo-matchers used in span queries.

## Matching Utilities

### `current_spans`

```python
whoosh.matching.current_spans(matcher) -> list
```

Returns a list of `Span` objects for the current match in `matcher`, or an
empty list if the matcher doesn't support positions.

### `disjunction_score`

```python
whoosh.matching.disjunction_score(matcher) -> float
```

Returns the sum of `matcher.score()` and the scores of all child matchers of
type `Union`.

### `intersection_score`

```python
whoosh.matching.intersection_score(matcher) -> float
```

Returns the sum of `matcher.score()` and all child matchers of type
`Intersection`.

### `child_count`

```python
whoosh.matching.child_count(matcher) -> int
```

Returns the number of child matchers in `matcher`.

### `has_quality`

```python
whoosh.matching.has_quality(matcher) -> bool
```

Returns `True` if `matcher` has a `query` attribute (i.e., is a
`QueryMatcher`-derived object, or a combination of such matchers).

### `has_untranslated`

```python
whoosh.matching.has_untranslated(matcher) -> bool
```

Returns `True` if the matcher has an `untranslated` attribute (set by
certain wrapper matchers like `TimeLimited`).

### `wrap`

```python
whoosh.matching.wrap(matcher)
```

Returns `matcher` if it has a `.copy()` method, otherwise wraps it in an
`AutoMatcher`.

### `wrap2`

```python
whoosh.matching.wrap2(a, b, m)
```

Returns either a `BinaryUnion2` or an `AutoMatcher` depending on whether `a`
and `b` are list-compatible.

### `unified`

```python
whoosh.matching.unified(matcher)
```

Returns `matcher` if it has an `untranslated` attribute, otherwise returns
`None`.

### `deletion`

```python
whoosh.matching.deletion(matcher)
```

If `matcher` has a `parent` attribute, returns the parent, otherwise returns
`None`.

### `AutoMatcher`

```python
class whoosh.matching.AutoMatcher(m, **kwargs)
```

A general-purpose matcher that wraps arbitrary objects and adds default
behavior for scoring, docnums, and other features. Created by `wrap()`.

### `MatchingTimeLimit`

```python
class whoosh.matching.MatchingTimeLimit
```

A lightweight exception raised when a query matcher exceeds a time limit.

### `TimeLimited`

```python
class whoosh.matching.TimeLimited(child, maxsteps=100, timeout=None, currenttime=None)
```

Wrapper that wraps a `Matcher` to enforce a time limit. Raises
`MatchingTimeLimit` if the time limit is exceeded.

**Parameters:**
- `child`: The matcher to wrap.
- `maxsteps`: Check time every N documents (default `100`).
- `timeout`: Maximum time in seconds (default `None`, no limit).
- `currenttime`: Optional function to use for getting the current time.

### `TermMatcher`

```python
class whoosh.matching.TermMatcher(postings, text, qname, scorer=None, boost=1.0)
```

Matches documents containing a specific term.

**Constructor:**
- `postings`: A `Postings` object from the index reader.
- `text`: The term text.
- `qname`: The query name for this term.
- `scorer`: Optional `Scorer` object.
- `boost`: Boost factor for this term's score.

### `MultiScorer`

```python
class whoosh.matching.MultiScorer(numgroups, start_i=0)
```

A `Scorer` that combines the scores from multiple scorers into one, weighted
across groups of segments.

### `RangeMatcher`

```python
class whoosh.matching.RangeMatcher(start_matcher, end_matcher, query)
```

Matches documents within a range of term values.

### `RegexMatcher`

```python
class whoosh.matching.RegexMatcher(regex, qname, boost=1.0)
```

Matches documents whose terms match a compiled regex.

### `SpanMatcher`

```python
class whoosh.matching.SpanMatcher(matcher, order=0, end=0)
```

Matches spans (positions) within documents.

### `SpanOverlap`

```python
class whoosh.matching.SpanOverlap(l, r)
```

Matches overlapping spans from two matchers.

### `SpanNear`

```python
class whoosh.matching.SpanNear(l, r, slop=1, ordered=True)
```

Matches spans that are near each other within a document.

### `SpanCondition`

```python
class whoosh.matching.SpanCondition(l, r)
```

Matches a condition on spans.

### `SpanBefore`

```python
class whoosh.matching.SpanBefore(l, r, end=0)
```

Matches spans before a given position.

### `SpanAfter`

```python
class whoosh.matching.SpanAfter(l, r, end=0)
```

Matches spans after a given position.

### `SpanOutside`

```python
class whoosh.matching.SpanOutside(l, r, end=0)
```

Matches spans outside a given range.

### `SpanFirst`

```python
class whoosh.matching.SpanFirst(l, start=0, end=1)
```

Matches spans at the beginning of a document.

### `SpanNot`

```python
class whoosh.matching.SpanNot(l, r)
```

Matches spans in `l` that are not in `r`.

### `SpanOr`

```python
class whoosh.matching.SpanOr(items)
```

Logical OR for span matchers.

### `SpanAnd`

```python
class whoosh.matching.SpanAnd(l, r)
```

Logical AND for span matchers.
