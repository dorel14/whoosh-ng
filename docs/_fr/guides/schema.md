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

Whoosh-NG v4.0.0.dev0 (en développement) introduit `SchemaBuilder` pour une API fluide :

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
writer.remove_field("legacy_field")

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

`ModelIndex` inspecte les annotations de type et les mappe vers des champs Whoosh :

| Type Python | Champ Whoosh |
|-------------|--------------|
| `str` | `TEXT` |
| `int` / `float` | `NUMERIC` |
| `bool` | `BOOLEAN` |
| `datetime` / `date` | `DATETIME` |
| `Decimal` | `NUMERIC(int, decimal_places=2)` |
| `Enum` | `KEYWORD` |
| `bytes` | `KEYWORD` (stockage hexadécimal) |
| `list[str]` | `KEYWORD` |
| `Optional[T]` | type mappé ou `STORED` |

Les champs ID sont auto-détectés : `SearchOptions(id=True)` explicite > nom `id`/`ID`/`_id` > premier champ `str`.

### Niveau 2 : Options explicites

Utilisez `SearchField` pour remplacer les valeurs par défaut :

```python
from whoosh_modern.models import SearchField, SearchOptions

class Book:
    title: str = SearchField(fulltext=True, stored=True)
    count: int = SearchField(sortable=True)
    tags: list[str] = SearchField(multi=True)
```

### Niveau 3 : Types annotés

Utilisez `Annotated` pour attacher des métadonnées directement aux annotations :

```python
from typing import Annotated
from whoosh_modern.models import SearchField

class Book:
    title: Annotated[str, SearchField(fulltext=True, stored=True)]
```

### Intégrations

#### Dataclass

```python
from dataclasses import dataclass
from whoosh_modern.models import ModelIndex

@dataclass
class Article:
    title: str
    body: str
    published: datetime.datetime

idx = ModelIndex(Article)
```

#### Pydantic v2

```python
from pydantic import BaseModel
from whoosh_modern.models import register_model

class Article(BaseModel):
    title: str
    body: str
    published: datetime.datetime

    # Métadonnées de recherche par champ via json_schema_extra
    model_config = {"json_schema_extra": {"search": {"fulltext": True}}}

idx = register_model(Article)
```

#### SQLAlchemy

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase
from whoosh_modern.models import register_model

class Base(DeclarativeBase):
    pass

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    title = Column(String, info={"search": {"fulltext": True, "stored": True}})
    published = Column(DateTime, info={"search": {"sortable": True}})

idx = register_model(Article)
```

#### SQLModel

```python
from sqlmodel import SQLModel, Field
from whoosh_modern.models import register_model

class Article(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str = Field(sa_column_kwargs={"info": {"search": {"fulltext": True}}})
    published: datetime.datetime

idx = register_model(Article)
```

#### msgspec

```python
import msgspec
from whoosh_modern.models import register_model

class Article(msgspec.Struct):
    title: str = msgspec.field(metadata={"search": {"fulltext": True}})
    published: datetime.datetime

idx = register_model(Article)
```

### Conversion d'instances

```python
doc = idx.to_whoosh_document(book_instance)
writer.add_document(**doc)
```

`to_whoosh_document` gère :
- dataclass : itération via `dataclasses.fields()`
- Pydantic/SQLModel : itération via `model_fields`
- SQLAlchemy : itération via `__mapper__.columns`
- Valeurs Enum converties en `.value`
- `bytes` convertis en chaîne hexadécimale

## Bonnes pratiques

1. **Minimal** : N'indexez que ce que vous cherchez
2. **STORED avec parcimonie** : Augmente la taille de l'index
3. **Champs uniques** : Utilisez `unique=True` pour les identifiants
4. **Boost de champ** : Boostez les champs importants au niveau schéma
5. **TEXT options** : Désactivez `phrase` si vous n'avez pas besoin de recherche de phrase
6. **Champ ID** : Laissez `ModelIndex` auto-détecter ou marquez explicitement avec `SearchOptions(id=True)`
