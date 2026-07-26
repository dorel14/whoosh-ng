---
color_scheme: dark
title: "API Champs"
nav_order: 2
parent: "Référence API"
lang: fr
---

# API Champs

Définissez la structure de votre index avec les types de champs.

## Schema

```python
class whoosh.fields.Schema
```

Définit les champs disponibles dans l'index.

### Méthodes

#### `add()`

```python
schema.add(fieldname, fieldtype, glob=False, **kwargs)
```

Ajoute un champ. Si `glob=True`, le nom est traité comme un pattern glob.

#### `remove()`

```python
schema.remove(fieldname, **kwargs)
```

Supprime un champ.

#### `items()`

```python
for name, field in schema.items():
    print(name, field)
```

Retourne les paires (nom, objet champ).

## Types de champs

### TEXT

```python
TEXT(
    stored=False,
    unique=False,
    phrase=True,
    analyzer=None,
    field_boost=1.0
)
```

Texte libre avec tokenisation et recherche de phrase optionnelle.

**Exemple:**
```python
titre = TEXT(stored=True)
corps = TEXT(analyzer=StemmingAnalyzer(), phrase=False)
```

### ID

```python
ID(stored=False, unique=False, field_boost=1.0)
```

Identifiant non tokenisé. Stocke la valeur entière comme terme unique.

**Exemple:**
```python
chemin = ID(stored=True, unique=True)
slug = ID(stored=True)
```

### KEYWORD

```python
KEYWORD(
    stored=False,
    lowercase=False,
    commas=False,
    scorable=False,
    field_boost=1.0
)
```

Mots-clés séparés par espace ou virgule.

**Exemple:**
```python
tags = KEYWORD(lowercase=True, commas=True, stored=True)
```

### STORED

```python
STORED(stored=True)
```

Champ stocké uniquement, non indexé ni searchable.

### NUMERIC

```python
NUMERIC(numtype=int, stored=False, unique=False, field_boost=1.0)
```

Champ numérique (entier ou flottant).

### DATETIME

```python
DATETIME(stored=False, unique=False, field_boost=1.0)
```

Champ date/heure.

### BOOLEAN

```python
BOOLEAN(stored=False, unique=False, field_boost=1.0)
```

Champ booléen. Searchable avec `oui`, `non`, `vrai`, `faux`, `1`, `0`, `t`, `f`.

### VectorField

```python
VectorField(
    dimensions: int,
    metric: str = "cosine",
    provider: str = "numpy",
    stored: bool = False
)
```

Champ pour embeddings vectoriels.

**Exemple:**
```python
embedding = VectorField(dimensions=384, metric="cosine", stored=True)
```

## SchemaBuilder

API fluent pour construire des schémas :

```python
from whoosh.fields import SchemaBuilder, TEXT, ID, NUMERIC

schema = (
    SchemaBuilder()
    .field("titre", TEXT(stored=True))
    .field("chemin", ID(stored=True, unique=True))
    .field("contenu", TEXT)
    .field("note", NUMERIC(float, stored=True))
    .build()
)
```

## Attributs de FieldType

| Attribut | Type | Description |
|----------|------|-------------|
| `format` | `Format` | Définit l'indexation |
| `vector` | `Format` | Format vectoriel optionnel |
| `scorable` | `bool` | Stocke la longueur pour BM25F |
| `stored` | `bool` | Stocke la valeur |
| `unique` | `bool` | Identifie les documents de façon unique |
