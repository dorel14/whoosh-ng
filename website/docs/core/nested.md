---
title: "Nested Documents"
sidebar_position: 31
---

# Nested Documents

This guide covers indexing and searching hierarchical/nested document
structures (e.g., a parent document with multiple child documents) using
Whoosh's parent-child relationship features.

## Defining Nested Documents

You can index parent documents that contain child documents by using a
parent field and child fields:

```python
from whoosh import fields, index

schema = fields.Schema(
    type=fields.ID(sortable=True),
    title=fields.TEXT(stored=True),
    content=fields.TEXT,
    section_name=fields.ID,
    section_content=fields.TEXT,
)
```

The `type` field distinguishes parent documents from child documents.

## Indexing Nested Documents

Use `IndexWriter.add_all()` with a generator that yields parent and child
documents grouped together:

```python
writer = ix.writer()
writer.add_all([
    parent_doc,
    child_doc_1,
    child_doc_2,
    parent_doc_2,
    child_doc_3,
])
```

Parent documents have `type="parent"` and child documents have
`type="child"`.

## Searching Nested Documents

### Parent-Query Child-Search

Search within child documents and match their parents:

```python
from whoosh.query import Every, Term
from whoosh.sorting import NestedParent

# Match all parent documents
parents = NestedParent(Term("type", "parent"))
q = Every("section_content", "hello")
results = searcher.search(q, sortedby=parents)
```

### Child-Query Parent-Search

Search for parent documents whose children match:

```python
from whoosh.sorting import NestedChildren

# Match parent documents that have children matching the query
parent_results = searcher.search(child_query, groupedby=NestedChildren(parent_matcher, child_matcher))
```

## Parent-Child Relationships at Index Time

When writing documents, use the `parent` parameter to link children to
parents:

```python
writer.add_document(type="parent", title="Chapter 1", _key="chapter1")
writer.add_document(type="child", section_name="Section 1.1",
                    section_content="...", parent="chapter1")
writer.add_document(type="child", section_name="Section 1.2",
                    section_content="...", parent="chapter1")
```

## Accessing Nested Results

To retrieve child matches alongside parent results, use the `expand` method
on the results:

```python
results = searcher.search(parent_query)
expanded = results.expand_child("section")
```

## Nested Faceting

Combine parent-child relationships with faceting using `NestedParent` and
`NestedChildren` as facets:

```python
parent_facet = NestedParent(FieldFacet("type"))
results = searcher.search(query, groupedby=parent_facet)
```

## Performance Considerations

- Parent-child joins are more expensive than flat document searches
- Use `childperm` searcher option to limit the number of permutations
  examined
- Consider whether hierarchical structure is needed at query time, or
  whether documents can be flattened during indexing
