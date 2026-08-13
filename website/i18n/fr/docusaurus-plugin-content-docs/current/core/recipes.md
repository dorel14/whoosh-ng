---
title: "Whoosh Recipes"
sidebar_position: 17
Module: whoosh
Version: 2.7.4
---
> **Note de traduction** : Cette page n'est pas encore traduite en francais.
> Le contenu anglais est affiche ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# Whoosh recipes

A collection of small, practical code snippets for common tasks.

## General

### Get the stored fields for a document from the document number

```python
stored_fields = searcher.stored_fields(docnum)
```

## Analysis

### Eliminate words shorter/longer than N

Use a `StopFilter` and the `minsize` and `maxsize` keyword arguments. If you
just want to filter based on size and not common words, set the `stoplist` to
`None`:

```python
sf = analysis.StopFilter(stoplist=None, minsize=2, maxsize=40)
```

### Allow optional case-sensitive searches

Index both the original and lowercased versions of each word. If the user
searches for an all-lowercase word, it acts as a case-insensitive search, but
if they search for a word with any uppercase characters, it acts as a
case-sensitive search:

```python
class CaseSensitivizer(analysis.Filter):
    def __call__(self, tokens):
        for t in tokens:
            yield t
            if t.mode == "index":
                low = t.text.lower()
                if low != t.text:
                    t.text = low
                    yield t

ana = analysis.RegexTokenizer() | CaseSensitivizer()
print([t.text for t in ana("The new SuperTurbo 5000", mode="index")])
# ["The", "the", "new", "SuperTurbo", "superturbo", "5000"]
```

## Searching

### Find every document

```python
myquery = query.Every()
```

### iTunes-style search-as-you-type

Use `whoosh.analysis.NgramWordAnalyzer` as the analyzer for the field you want
to search as the user types. You can save space in the index by turning off
positions in the field using `phrase=False`:

```python
# For example, to search the "title" field as the user types
analyzer = analysis.NgramWordAnalyzer()
title_field = fields.TEXT(analyzer=analyzer, phrase=False)
schema = fields.Schema(title=title_field)
```

See the documentation for the `NgramWordAnalyzer` class for information on the
available options. Also see [N-grams](/core/ngrams).

## Shortcuts

### Look up documents by a field value

```python
# Single document (unique field value)
stored_fields = searcher.document(id="bacon")

# Multiple documents
for stored_fields in searcher.documents(tag="cake"):
    ...
```

## Sorting and scoring

See [Sorting](/core/sorting).

### Score results based on the position of the matched term

The following scoring function uses the position of the first occurrence of a
term in each document to calculate the score, so documents with the given term
earlier in the document will score higher:

```python
from whoosh import scoring

def pos_score_fn(searcher, fieldname, text, matcher):
    poses = matcher.value_as("positions")
    return 1.0 / (poses[0] + 1)

pos_weighting = scoring.FunctionWeighting(pos_score_fn)
with myindex.searcher(weighting=pos_weighting) as s:
    ...
```

## Results

### How many hits were there?

```python
# The number of scored hits
found = results.scored_length()

if results.has_exact_length():
    print("Scored", found, "of exactly", len(results), "documents")
else:
    low = results.estimated_min_length()
    high = results.estimated_length()
    print("Scored", found, "of between", low, "and", high, "documents")
```

### Which terms matched in each hit?

```python
# Use terms=True to record term matches for each hit
results = searcher.search(myquery, terms=True)

for hit in results:
    # Which terms matched in this hit?
    print("Matched:", hit.matched_terms())
    # Which terms from the query didn't match in this hit?
    print("Didn't match:", myquery.all_terms() - hit.matched_terms())
```

## Global information

### How many documents are in the index?

```python
# Including documents that are deleted but not yet optimized away
numdocs = searcher.doc_count_all()
# Not including deleted documents
numdocs = searcher.doc_count()
```

### What fields are in the index?

```python
return myindex.schema.names()
```

### Is term X in the index?

```python
return ("content", "wobble") in searcher
```

### How many times does term X occur in the index?

```python
# Number of times content:wobble appears in all documents
freq = searcher.frequency("content", "wobble")
# Number of documents containing content:wobble
docfreq = searcher.doc_frequency("content", "wobble")
```

### Is term X in document Y?

```python
# Without term vectors
postings = searcher.postings("content", "wobble")
postings.skip_to(500)
return postings.id() == 500

# If field has term vectors
vector = searcher.vector(500, "content")
vector.skip_to("wobble")
return vector.id() == "wobble"
```

## See also

- [Analysis](/core/analysis) â€” Analyzers, tokenizers, and filters
- [N-grams](/core/ngrams) â€” Search-as-you-type with N-gram analyzers
- [Searching](/core/searching) â€” The `search()` method and `Hit` objects

