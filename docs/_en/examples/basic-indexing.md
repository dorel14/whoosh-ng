---
title: "Basic Indexing"
nav_order: 200
---

# Basic Indexing

Examples for indexing documents in Whoosh‑NG. Each section is a self-contained, **runnable** script.

> **Real-world scenario**: You're building a blog search engine. You have a CSV file
> of articles (`blog_posts.csv`) with `title`, `url`, `tags`, and `body` columns.

## 1. Define a Production Schema

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC, DATETIME
from datetime import datetime

# Stored=True keeps the field value in the index so you can retrieve it
# in search results without querying an external DB.
schema = Schema(
    doc_id=ID(stored=True, unique=True),     # primary key
    title=TEXT(stored=True),                  # full-text searchable + retrievable
    url=ID(stored=True),                      # stored only, no full-text analysis
    tags=KEYWORD(stored=True, commas=True),   # multi-value: "python,search,guide"
    body=TEXT(stored=True, phrase=True),      # searchable text with phrase queries
    published_at=DATETIME(stored=True, sortable=True),
    word_count=NUMERIC(int, stored=True),
)
```

## 2. Build an Index from a CSV File

```python
import csv
import shutil
from whoosh import index

# Clean prior index (development only!)
shutil.rmtree("blog_index", ignore_errors=True)
ix = index.create_in("blog_index", schema)

# Simulate a CSV file with blog post data
# blog_posts.csv:
#   doc_id,title,url,tags,published_at,word_count,body
#   1,Building a Search Engine,/posts/1,python,search,2024-01-15,1200,"Learn how to build..."
#   2,Python Tips,/posts/2,python,tips,2024-02-20,800,"Ten tips for Python..."

with open("blog_posts.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    with ix.writer() as writer:
        for row in reader:
            writer.add_document(
                doc_id=row["doc_id"],
                title=row["title"],
                url=row["url"],
                tags=row["tags"],
                published_at=datetime.fromisoformat(row["published_at"]),
                word_count=int(row["word_count"]),
                body=row["body"],
            )
        writer.commit()
```

## 3. Incremental Update — Re-index Modified Documents

```python
# Suppose your CMS tells you which posts were updated since the last sync
updated_posts = [
    {"doc_id": "1", "title": "Building a Search Engine (Updated)", "body": "Updated content..."},
    {"doc_id": "3", "title": "New Post", "body": "Fresh content..."},
]

with ix.writer() as writer:
    for post in updated_posts:
        writer.update_document(
            doc_id=post["doc_id"],
            title=post["title"],
            url=f"/posts/{post['doc_id']}",
            tags="python,search",
            published_at=datetime(2024, 6, 1),
            word_count=len(post["body"].split()),
            body=post["body"],
        )
    writer.commit()
```

## 4. Delete Documents by Term

```python
from whoosh.query import Term

# Remove a post by its unique doc_id
with ix.writer() as writer:
    writer.delete_by_term("doc_id", "3")
    writer.commit()
```

## 5. Bulk Insert for Large Datasets (10k+ Documents)

```python
from whoosh.writing import BufferedWriter

# Use BufferedWriter for high-throughput indexing.
# It buffers documents and commits in batches.
buffered = BufferedWriter(ix, period=60, limit=500)

try:
    for doc in large_dataset:  # your generator/list of dicts
        with buffered:
            buffered.add_document(
                doc_id=doc["doc_id"],
                title=doc["title"],
                url=doc["url"],
                tags=",".join(doc["tags"]),
                published_at=doc["published_at"],
                word_count=doc["word_count"],
                body=doc["body"],
            )
finally:
    buffered.close()
```

## 6. Run a Search on the Indexed Data

```python
from whoosh.qparser import QueryParser

ix = index.open_dir("blog_index")

with ix.searcher() as s:
    qp = QueryParser("body", ix.schema)
    q = qp.parse("search engine")

    results = s.search(q, limit=10)
    for hit in results:
        print(f"Title: {hit['title']}")
        print(f"URL:   {hit['url']}")
        print(f"Score: {hit.score:.3f}")
        print(f"Snippet: {hit.highlights('body')}")
        print("---")

