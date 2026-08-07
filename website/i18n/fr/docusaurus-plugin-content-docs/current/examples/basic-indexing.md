---
title: "Indexation de base"
sidebar_position: 200
---

# Indexation de base

Exemples pour indexer des documents dans Whoosh‑NG. Chaque section est un script
autonome **exécutable**.

> **Scénario concret** : Vous construisez un moteur de recherche de blog. Vous avez
> un fichier CSV d'articles (`blog_posts.csv`) avec les colonnes `title`, `url`,
> `tags`, `body` et `published_at`.

## 1. Schéma de production

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC, DATETIME
from datetime import datetime

schema = Schema(
    doc_id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    url=ID(stored=True),
    tags=KEYWORD(stored=True, commas=True),
    body=TEXT(stored=True, phrase=True),
    published_at=DATETIME(stored=True, sortable=True),
    word_count=NUMERIC(int, stored=True),
)
```

## 2. Créer l'index

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, KEYWORD, NUMERIC, DATETIME
import shutil

shutil.rmtree("blog_index", ignore_errors=True)
ix = index.create_in("blog_index", schema)
```

## 3. Indexer depuis un CSV

```python
import csv
from datetime import datetime

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

## 4. Mise à jour incrémentale

```python
updated_posts = [
    {"doc_id": "1", "title": "Titre mis à jour", "body": "Nouveau contenu..."},
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

## 5. Suppression

```python
from whoosh.query import Term

with ix.writer() as writer:
    writer.delete_by_term("doc_id", "3")
    writer.commit()
```

## 6. Indexation en bloc (10k+ documents)

```python
from whoosh.writing import BufferedWriter

buffered = BufferedWriter(ix, period=60, limit=500)
try:
    for doc in large_dataset:
        with buffered:
            buffered.add_document(**doc)
finally:
    buffered.close()
```

## 7. Recherche sur les données indexées

```python
from whoosh.qparser import QueryParser

ix = index.open_dir("blog_index")

with ix.searcher() as s:
    qp = QueryParser("body", ix.schema)
    q = qp.parse("moteur de recherche")

    results = s.search(q, limit=10)
    for hit in results:
        print(f"{hit['title']} | {hit['url']} | score={hit.score:.3f}")
```
