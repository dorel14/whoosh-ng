---
color_scheme: dark
title: "API Requêtes"
nav_order: 5
parent: "Référence API"
lang: fr
---

# API Requêtes

Construisez des requêtes complexes avec l'API de Whoosh-NG.

## Classes principales

### Query

Classe de base pour toutes les requêtes.

```python
class whoosh.query.Query
```

#### Méthodes

| Méthode | Description |
|---------|-------------|
| `q.all(methodname, *args)` | Applique une méthode à tous les termes |
| `q.normalize()` | Normalise la représentation textuelle |
| `q.replace(fieldname, old, new)` | Remplace un terme |
| `q.exclude(term)` | Exclut un terme spécifique |
| `q.fieldname` | Champ principal de la requête |
| `q.children()` | Requêtes enfants (pour opérateurs) |

## Requêtes booléennes

### And

```python
And(require, boost=1.0)
# Tous doivent matcher
```

### Or

```python
Or(require, boost=1.0)
# Un seul doit matcher
```

### Not

```python
Not(require, exclude=None)
```

### Requête Term

```python
Term(fieldname, text, boost=1.0)
```

## Plages

### NumericRange

```python
NumericRange(fieldname, start, end, startexcl=False, endexcl=False)
```

### DateRange

```python
DateRange(fieldname, start, end, startexcl=False, endexcl=False)
```

## Phrase et proximité

### Phrase

```python
Phrase(fieldname, words, slop=1, boost=1.0)
```

### Distance / Near

### Prefix

```python
Prefix(fieldname, text, boost=1.0)
```

## Combinateurs avancés

### Every

```python
Every(fieldname, boost=1.0)
```

### Null

```python
NullQuery
```

## Opérateurs de requête globaux

| Requête | Description |
|---------|-------------|
| `Term` | Égalité exacte (pas d'analyse) |
| `Variations` | Variantes lexicales |
| `FuzzyTerm` | Recherche floue |
| `Wildcard` | Jokers (lent sur grands corpus) |
| `Regex` | Expression régulière |

## Construction manuelle

```python
from whoosh.query import (
    Term, And, Or, Not, Phrase, NumericRange, DateRange
)

q = And([
    Term("status", "published"),
    NumericRange("date", 2020, 2025),
    Or([Term("tags", "python"), Term("tags", "recherche")]),
    Phrase("content", ["tutoriel", "whoosh"])
])
```
