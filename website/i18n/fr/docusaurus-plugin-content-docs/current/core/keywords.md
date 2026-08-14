---
title: "Query Expansion & Keywords"
sidebar_position: 13
Module: whoosh.classify, whoosh.searching
Version: 2.7.4
---
> **Note de traduction** : Cette page n'est pas encore traduite en francais.
> Le contenu anglais est affiche ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# Query expansion and keyword extraction

## Overview

Whoosh provides methods for computing the "key terms" of a set of documents.
For these methods, "key terms" basically means terms that are frequent in the
given documents, but relatively infrequent in the indexed collection as a whole.

Because this is a purely statistical operation, not a natural language
processing or AI function, the quality of the results will vary based on the
content, the size of the document collection, and the number of documents for
which you extract keywords.

These methods can be useful for providing the following features to users:

- **Search term expansion.** Extract key terms for the top N results from a
  query and suggest them to the user as additional/alternate query terms.
- **Tag suggestion.** Extracting the key terms for a single document may yield
  useful suggestions for tagging the document.
- **"More like this".** Extract key terms for the top ten or so results from a
  query (and removing the original query terms), and use those key words as the
  basis for another query that may find more documents using terms the user
  didn't think of.

## Usage

### More like this

Get more documents like a certain search hit. *This requires that the field you
want to match on is vectored or stored, or that you have access to the original
text.*

```python
results = mysearcher.search(myquery)
first_hit = results[0]
more_results = first_hit.more_like_this("content")
```

### Key terms from top N results

*This requires that the field is either vectored or stored.*

```python
# Extract five key terms from the "content" field of the top ten documents
keywords = [keyword for keyword, score
            in results.key_terms("content", docs=10, numterms=5)]
```

### Key terms from an arbitrary set of documents

*This requires that the field is either vectored or stored.*

```python
with email_index.searcher() as s:
    docnums = s.document_numbers(emailto="matt@whoosh.ca")
    keywords = [keyword for keyword, score
                in s.key_terms(docnums, "body")]
```

### Key terms from arbitrary text not in the index

```python
with email_index.searcher() as s:
    keywords = [keyword for keyword, score
                in s.key_terms_from_text("body", mytext)]
```

## Expansion models

The `ExpansionModel` subclasses in the `whoosh.classify` module implement
different weighting functions for key words. These models are translated into
Python from original Java implementations in Terrier.

```python
from whoosh.classify import Bo1Model

results = mysearcher.search(myquery)
keywords = results.key_terms("content", docs=10, numterms=5, model=Bo1Model)
```

Available models include `Bo1Model`, `Bo2Model`, and `KLModel`.

## See also

- [Searching](/core/searching) â€” `Results`, `Hit`, and the `search()` method
- [API: searching](../api/searching) â€” `key_terms`, `more_like_this` reference
