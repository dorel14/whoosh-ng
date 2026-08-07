---
title: "Formats API"
sidebar_position: 190
---

# Formats API

Classes that control how posting information (frequencies, positions,
character offsets, and weights) is encoded and stored for each field in the
index. The `Format` object is a factory and encoder/decoder for the
value strings stored alongside each posting.

## Module Functions

### `tokens`

```python
whoosh.formats.tokens(value, analyzer, kwargs)
```

Takes a text `value` and an `analyzer`, runs the analyzer on the value, and
returns the resulting token generator (wrapped with `unstopped()` to ignore
`STOP` tokens). Used internally by `Format.word_values()`.

## Format Classes

All format classes accept a `field_boost` parameter (default `1.0`) that
scales the score of all queries matching terms in that field.

### `Format`

```python
class whoosh.formats.Format(field_boost=1.0, **options)
```

Abstract base class for all posting formats. Format objects are
field-level objects: one is created per `Field` and shared across all
postings for that field.

**Attributes:**
- `posting_size (int)`: Fixed byte size of encoded postings, or `None`/`-1`
  if variable-size.
- `textual (bool)`: Whether this format expects string tokens (vs. bytes).
  Default `True`.

**Methods:**

#### `word_values(value, analyzer, **kwargs)`

Abstract. Takes a text value, runs it through the analyzer, and yields
`(tokentext, frequency, weight, valuestring)` tuples.

#### `encode(value)`

Abstract. Encodes raw posting data into the value string bytes.

#### `decode_frequency(valuestring)`

Abstract. Decodes the frequency (term count in document) from the value
string.

#### `decode_weight(valuestring)`

Abstract. Decodes the weight (total boost contribution) from the value string.

#### `combine(valuestrings)`

Abstract. Combines multiple value strings (from overlapping segments) into
a single value string.

#### `supports(name)`

Returns `True` if this format supports interpreting its postings as `name`
(e.g., `"frequency"`, `"positions"`, `"characters"`, `"position_boosts"`,
`"character_boosts"`). Equivalent to `hasattr(self, "decode_" + name)`.

#### `decoder(name)`

Returns the `decode_<name>` method for the given attribute name.

#### `decode_as(astype, valuestring)`

Calls the appropriate `decode_<astype>` method on `valuestring` and returns
the result.

#### `fixed_value_size()`

Returns `self.posting_size` if positive, otherwise `None`.

#### `__eq__(other)`

Returns `True` if `other` is the same class with equal `__dict__`.

### `Existence`

```python
class whoosh.formats.Existence(field_boost=1.0, **options)
```

Indexes only whether a term occurred in a document—not its frequency or
positions. Useful for non-scorable fields like paths.

- `posting_size = 0`
- Supports: `frequency` (always 1), `weight` (always `field_boost`)
- `encode()` returns empty bytes

### `Frequency`

```python
class whoosh.formats.Frequency(field_boost=1.0, boost_as_freq=False, **options)
```

Stores term frequency information (term count per document) for each posting.

- `posting_size = _INT_SIZE` (4 bytes)
- Supports: `frequency`, `weight`
- `encode()` encodes the count as a packed unsigned int
- `boost_as_freq`: If `True`, boosts are interpreted as frequency boosts

```python
from whoosh.formats import Frequency
fmt = Frequency(field_boost=1.0)
```

### `Positions`

```python
class whoosh.formats.Positions(field_boost=1.0, **options)
```

Stores position information (term offsets within the document) in each
posting, enabling phrase queries and "near" queries.

- Supports: `frequency`, `weight`, `positions`, `position_boosts`
- `encode(poslist)` encodes positions using variable-length delta encoding
- Positions are stored as delta-encoded variable-length integers

```python
from whoosh.formats import Positions
fmt = Positions()
```

### `Characters`

```python
class whoosh.formats.Characters(field_boost=1.0, **options)
```

Extends `Positions` to also store character start and end offsets for each
term occurrence, enabling character-precise highlighting.

- Supports: `frequency`, `weight`, `positions`, `position_boosts`,
  `characters`
- `encode()` encodes (position, startchar, endchar) triples with delta
  encoding

### `PositionBoosts`

```python
class whoosh.formats.PositionBoosts(field_boost=1.0, **options)
```

Extends `Positions` to store per-position boost values in addition to
positions.

- Supports: `frequency`, `weight`, `positions`, `position_boosts`
- `encode()` encodes `(position, boost)` pairs

### `CharacterBoosts`

```python
class whoosh.formats.CharacterBoosts(field_boost=1.0, **options)
```

Extends `Characters` to store per-position boost values along with
character offsets.

- Supports: `frequency`, `weight`, `positions`, `position_boosts`,
  `characters`, `character_boosts`
- `encode()` encodes `(position, startchar, endchar, boost)` tuples
