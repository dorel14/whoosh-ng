---
title: "Classify API"
nav_order: 230
---

# Classify API

Classes and functions for classifying and extracting information from
documents. This module provides query expansion models, similarity
functions (shingling, simhash), and clustering algorithms.

## Expansion Models

### `ExpansionModel`

```python
class whoosh.classify.ExpansionModel(doc_count, field_length)
```

Abstract base class for query expansion models. Subclass to implement custom
expansion scoring.

**Constructor:**
- `doc_count`: Total number of documents in the collection.
- `field_length`: Total length of the field across all documents.

**Computed Attributes:**
- `N`: Document count.
- `collection_total`: Total field length.
- `mean_length`: Average field length (`collection_total / N`).

**Methods:**
- `normalizer(maxweight, top_total)`: Returns a normalization factor.
- `score(weight_in_top, weight_in_collection, top_total)`: Returns the
  expansion score for a term.

### `Bo1Model`

```python
class whoosh.classify.Bo1Model(doc_count, field_length)
```

Bayesian One-Poisson expansion model. One of the standard query expansion
models.

### `Bo2Model`

```python
class whoosh.classify.Bo2Model(doc_count, field_length)
```

Bayesian Two-Poisson expansion model. Another standard query expansion model.

### `KLModel`

```python
class whoosh.classify.KLModel(doc_count, field_length)
```

Kullback-Leibler divergence-based expansion model.

## Expander

### `Expander`

```python
class whoosh.classify.Expander(
    ixreader,
    fieldname,
    model=Bo1Model
)
```

Uses an `ExpansionModel` to expand the set of query terms based on the top N
result documents.

**Constructor:**
- `ixreader`: An `IndexReader` object.
- `fieldname`: The name of the field to expand terms from.
- `model`: An `ExpansionModel` class or instance. Defaults to `Bo1Model`.

**Methods:**

#### `add(vector)`

Adds forward-index information about one of the "top N" documents.

- `vector`: A series of `(text, weight)` tuples, such as is returned by
  `Reader.vector_as("weight", docnum, fieldname)`.

#### `add_document(docnum)`

Adds a document's term vector to the expander. If the field has a term vector,
uses it; otherwise falls back to stored field text.

#### `add_text(string)`

Adds a text string by indexing it with the field's analyzer.

#### `expanded_terms(number, normalize=True)`

Returns the N most important terms in the vectors added so far, ranked by
the expansion model's score.

- `number`: Number of terms to return.
- `normalize`: Whether to normalize weights.
- Returns: List of `(term, weight)` tuples, sorted by weight descending.

```python
from whoosh.classify import Expander, Bo1Model

expander = Expander(ix.reader(), "content")
for docnum in results.ids()[:10]:
    expander.add_document(docnum)

for word, weight in expander.expanded_terms(5):
    print(word, weight)
```

## Similarity Functions

### `shingles`

```python
whoosh.classify.shingles(input, size=2) -> iterable
```

Generates `(shingle, frequency)` pairs from a string by sliding a window of
the given size over the input.

**Parameters:**
- `input`: The input string.
- `size`: The shingle size (default `2`).

```python
from whoosh.classify import shingles

for shingle, freq in shingles("hello world", size=2):
    print(shingle, freq)
```

### `simhash`

```python
whoosh.classify.simhash(features, hashbits=32) -> int
```

Computes a simhash (perceptual hash) from a sequence of weighted features.
Simhashes that are similar produce similar hash values, allowing fast
near-duplicate detection via Hamming distance.

**Parameters:**
- `features`: Iterable of `(feature, weight)` tuples.
- `hashbits`: Number of bits in the hash (default `32`).
- Returns: An integer hash value.

```python
from whoosh.classify import shingles, simhash

h1 = simhash(shingles(text1))
h2 = simhash(shingles(text2))
from whoosh.classify import hamming_distance
dist = hamming_distance(h1, h2)
```

### `hamming_distance`

```python
whoosh.classify.hamming_distance(first_hash, other_hash, hashbits=32) -> int
```

Computes the Hamming distance between two hash values. A small distance
indicates high similarity.

**Parameters:**
- `first_hash`: First hash integer.
- `other_hash`: Second hash integer.
- `hashbits`: Number of bits in the hashes (default `32`).

## Clustering

### `kmeans`

```python
whoosh.classify.kmeans(
    data,
    k,
    t=0.0001,
    distfun=None,
    maxiter=50,
    centers=None
) -> (labels, centroids)
```

One-dimensional K-means clustering. Assigns each data point to the nearest
of `k` centroids and returns cluster labels and final centroids.

**Parameters:**
- `data`: List of data points (numeric values).
- `k`: Number of clusters.
- `t`: Tolerance; stops if centroid changes are below this value.
- `distfun`: Optional distance function (unused if `None`).
- `maxiter`: Maximum iterations (default `50`).
- `centers`: Optional list of initial centroids. If `None`, selects `k`
  random points from `data`.

**Returns:** A tuple `(labels, centroids)` where `labels` is a list of
cluster assignments per data point and `centroids` is the list of final
centroid positions.

### `two_pass_variance`

```python
whoosh.classify.two_pass_variance(data) -> float
```

Computes the sample variance of a data list using the two-pass algorithm
(first pass computes the mean, second pass accumulates squared deviations).

### `weighted_incremental_variance`

```python
whoosh.classify.weighted_incremental_variance(data_weight_pairs) -> float
```

Computes the weighted variance incrementally from a sequence of
`(value, weight)` pairs.

### `swin`

```python
whoosh.classify.swin(data, size) -> list
```

Sliding window clustering that groups data points where the range (max - min)
within a window of `size` is below a threshold. Uses variance for ranking.

**Parameters:**
- `data`: Sorted list of data points.
- `size`: Maximum window range (max - min) for clustering.

**Returns:** A list of `(left, right, count, variance)` tuples representing
clusters, sorted by count descending then by variance ascending.
