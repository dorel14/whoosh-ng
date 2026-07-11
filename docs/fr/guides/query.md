---
title: "Langage de requête"
nav_order: 25
parent: "Guides"
lang: fr
---

# Langage de requête

Whoosh-NG fournit un langage de requête puissant similaire à Lucene, ainsi qu'une API de requêtes programmatique.

## Syntaxe de requête

### Termes de base

```
bonjour                    # Terme unique
bonjour monde              # Termes multiples (AND par défaut)
bonjour OU monde           # OR explicite
"bonjour monde"            # Phrase
```

### Spécification de champ

```
titre:python               # Recherche dans le champ titre
titre:"Tutoriel Python"    # Phrase dans un champ spécifique
```

### Opérateurs booléens

```
python AND whoosh
python OR whoosh
python AND NOT java
python AND (whoosh OR lucene)
```

### Préfixe et jokers

```
pyth*                     # Requête préfixe
pyth?n                    # Joker caractère unique
```

### Requêtes de plage

```
date:[2020 TO 2025]
prix:[10 TO 50]
rating:[4.0 TO *]         # Plage ouverte
```

### Recherche floue

```
python~2                  # Distance d'édition <= 2
lucene~1                  # Correspondance approximative
```

### Recherche de proximité

```
"bonjour monde"~5         # Dans un rayon de 5 termes
```

### Boost

```
python^2.0 whoosh         # Booster python par 2x
(titre:python)^3 content:python  # Booster les matches dans titre
```

## Classes de requêtes

Construisez des requêtes programmatiquement :

```python
from whoosh.query import *

# Terme simple
q = Term("content", "python")

# AND
q = And([Term("content", "python"), Term("content", "whoosh")])

# OR
q = Or([Term("content", "python"), Term("content", "lucene")])

# Phrase
q = Phrase("content", ["bonjour", "monde"])

# Plage
q = NumericRange("prix", 10, 50)
q = DateRange("date", datetime(2020,1,1), datetime(2025,1,1))

# Préfixe
q = Prefix("content", "pyth")
```

## MultifieldParser

Recherchez plusieurs champs avec des boosts différents :

```python
from whoosh.qparser import MultifieldParser

qp = MultifieldParser(
    ["titre", "content", "tags"],
    schema,
    fieldboosts={"titre": 2.0, "tags": 1.5}
)
q = qp.parse("python recherche")
```

## Échappement des caractères spéciaux

```
titre\:python              # Deux-points littéral
chemin\:\/\/exemple        # Échapper les caractères spéciaux
```
