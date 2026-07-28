---
title: "Conception de schéma"
nav_order: 30
lang: fr
---

# Conception de schéma

Le schéma définit la structure des documents dans votre index. Il spécifie les champs existants, leur indexation et leur stockage.

## Types de champs

| Type | Description | Indexé | Stocké |
|------|-------------|--------|--------|
| `TEXT` | Texte libre, tokenisé | Oui | Optionnel |
| `ID` | Identifiant non tokenisé | Oui | Optionnel |
| `KEYWORD` | Mots-clés séparés par espace/virgule | Oui | Optionnel |
| `STORED` | Stocké uniquement, non searchable | Non | Oui |
| `NUMERIC` | Entier ou flottant | Oui | Optionnel |
| `DATETIME` | Dates et heures | Oui | Optionnel |
| `BOOLEAN` | Booléen | Oui | Optionnel |
| `NGRAM` | N-grammes de caractères | Oui | Optionnel |
| `NGRAMWORDS` | N-grammes de mots | Oui | Optionnel |
| `VectorField` | Vecteur d'embedding | Personnalisé | Optionnel |

## Créer un schéma

```python
from whoosh.fields import Schema, TEXT, ID, KEYWORD, STORED, NUMERIC

schema = Schema(
    title=TEXT(stored=True),
    path=ID(stored=True, unique=True),
    content=TEXT,
    tags=KEYWORD(lowercase=True),
    published=NUMERIC(int, stored=True),
    is_published=BOOLEAN,
    icon=STORED
)
```

## Options des champs

### TEXT

```python
content = TEXT(
    stored=False,        # Stocker le texte original ?
    unique=False,        # Utiliser pour remplacer des documents ?
    phrase=True,         # Indexer les positions pour recherche de phrases
    analyzer=None,       # Analyseur personnalisé
    field_boost=1.0      # Boost pour le scoring
)
```

### ID

```python
path = ID(
    stored=True,         # Stocker le chemin
    unique=True          # Utiliser pour remplacement de documents
)
```

### KEYWORD

```python
tags = KEYWORD(
    stored=False,
    lowercase=True,      # Minusculiser automatiquement
    commas=True,         # Séparer par virgules
    scorable=True        # Stocker la longueur pour scoring
)
```

## SchemaBuilder

Whoosh-NG 4.0 introduit `SchemaBuilder` pour une API fluide :

```python
from whoosh.fields import SchemaBuilder, TEXT, ID, NUMERIC

schema = (
    SchemaBuilder()
    .field("title", TEXT(stored=True))
    .field("path", ID(stored=True, unique=True))
    .field("content", TEXT)
    .field("rating", NUMERIC(float, stored=True))
    .build()
)
```

## Champs dynamiques

Utilisez des patterns glob pour associer des types :

```python
# Tout champ finissant par "_date" est un DATETIME
schema.add("*_date", DATETIME(stored=True), glob=True)

# Tout champ finissant par "_id" est un ID
schema.add("*_id", ID(stored=True), glob=True)
```

## Modifier le schéma

Ajoutez ou supprimez des champs après création :

```python
writer = ix.writer()

# Ajouter un champ
writer.add_field("description", TEXT(stored=True))

# Supprimer un champ
writer.remove_field("deprecated_field")

writer.commit()
```

> Note: Supprimer un champ ne fait que le retirer du schéma. Les données ne sont libérées qu'à l'optimisation.

## Modèles de recherche

Whoosh-NG peut mapper automatiquement des modèles Python (dataclasses, Pydantic, SQLAlchemy, SQLModel, msgspec) vers un `Schema` Whoosh via `ModelIndex`.

### Niveau 1 : Auto-mapping

```python
from dataclasses import dataclass
from whoosh_modern.models import ModelIndex

@dataclass
class Book:
    title: str
    count: int
    tag: str | None = None

idx = ModelIndex(Book)
schema = idx.schema
```

### Niveau 2 : Options explicites

```python
from whoosh_modern.models import SearchField, SearchOptions

class Book:
    title: str = SearchField(fulltext=True, stored=True)
    count: int = SearchField(sortable=True)
    tag: str = SearchField(multi=True)
```

### Intégrations

```python
# Pydantic
from whoosh_modern.models import register_model
from pydantic import BaseModel

class BookModel(BaseModel):
    title: str
    year: int

idx = register_model(BookModel)

# SQLAlchemy
from sqlalchemy import Column, Integer, String
from whoosh_modern.models import register_model

class BookSQL:
    __tablename__ = "book"
    title = Column(String, info={"search": {"fulltext": True}})
    year = Column(Integer, info={"search": {"sortable": True}})

idx = register_model(BookSQL)
```

### Conversion d'instances

```python
doc = idx.to_whoosh_document(book_instance)
writer.add_document(**doc)
```

## Bonnes pratiques

1. **Minimal**: N'indexez que ce que vous cherchez
2. **STORED avec parcimonie**: Augmente la taille de l'index
3. **Champs uniques**: Utilisez `unique=True` pour les identifiants
4. **Boost de champ**: Boostez les champs importants au niveau schéma
5. **TEXT options**: Désactivez `phrase` si vous n'avez pas besoin de recherche de phrase

