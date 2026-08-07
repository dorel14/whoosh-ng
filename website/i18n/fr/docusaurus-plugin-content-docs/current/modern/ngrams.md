---
title: 'N-grammes'
sidebar_position: 100
---

# N-grammes

Ce guide couvre la tokenisation et l'analyse N-gramme pour la recherche
de sous-chaînes, les requêtes par préfixe et la fonctionnalité
d'autocomplétion.

## Qu'est-ce que les N-grammes ?

Un N-gramme est une séquence continue de N caractères (ou de jetons)
d'une chaîne. Par exemple, les 2-grammes de "hello" sont : "he", "el",
"ll", "lo".

L'analyse N-gramme est utile pour :
- Recherche de sous-chaînes (trouver "ell" dans "hello")
- Autocomplétion / suggestions en temps réel
- Correspondance floue sans calcul de distance d'édition

## NgramTokenizer

Le `NgramTokenizer` divise le texte en N-grammes au niveau des
caractères :

```python
from whoosh.analysis import NgramTokenizer
from whoosh import fields

tokenizer = NgramTokenizer(minsize=2, maxsize=4)

schema = fields.Schema(
    content=fields.TEXT(analyzer=tokenizer),
)
```

### Paramètres de NgramTokenizer

- `minsize` : Longueur minimale des N-grammes (par défaut `2`)
- `maxsize` : Longueur maximale des N-grammes (par défaut `4`)

Avec l'exemple ci-dessus, le texte "hello" produit ces 2-4-grammes :
`he, hel, hell, el, ell, ello, l, ll, llo, l, lo, o`

## NgramFilter

Le `NgramFilter` crée des N-grammes au niveau des mots à partir du
texte tokenisé :

```python
from whoosh.analysis import RegexTokenizer, NgramFilter

analyzer = RegexTokenizer() | NgramFilter(maxsize=2)
```

Cela produit des grammes au niveau des mots : pour "hello world", il
produit ("hello",) et ("hello", "world").

## NgramWordAnalyzer

Un analyseur de commodité qui combine `NgramTokenizer` avec
`LowercaseFilter` :

```python
from whoosh.analysis import NgramWordAnalyzer

analyzer = NgramWordAnalyzer(minsize=2, maxsize=4)

schema = fields.Schema(
    content=fields.TEXT(analyzer=analyzer),
)
```

## Cas d'utilisation

### Recherche de sous-chaînes

Avec l'analyse N-gramme, vous pouvez correspondre des sous-chaînes :

```python
from whoosh.qparser import QueryParser

# Index text with N-grams
# Searching for "ell" matches "hello" because "ell" is a substring
qp = QueryParser("content", schema=ix.schema)
q = qp.parse("ell")
results = searcher.search(q)
```

### Correspondance par préfixe

Définissez `maxsize` à une grande valeur pour créer efficacement des
N-grammes de préfixe :

```python
from whoosh.analysis import NgramWordAnalyzer

# Create N-grams where each word's prefixes become searchable tokens
# e.g., "hello" -> "h", "he", "hel", "hell", "hello"
analyzer = NgramWordAnalyzer(minsize=1, maxsize=10)
```

### Autocomplétion

Les index N-gramme sont couramment utilisés pour l'autocomplétion.
Pour une autocomplétion plus avancée avec des N-grammes de bord
(edge n-grams), envisrez :

```python
from whoosh.analysis import RegexTokenizer, NgramFilter
from whoosh.query import Prefix

# Index with standard tokenization, then use Prefix queries for autocomplete
analyzer = RegexTokenizer()
schema = fields.Schema(
    title=fields.TEXT(stored=True, analyzer=analyzer),
    content=fields.TEXT(analyzer=analyzer),
)

# For autocomplete, query with Prefix
from whoosh.qparser import QueryParser
qp = QueryParser("title", schema=ix.schema)
q = Prefix("title", "hel")  # Find documents where title starts with "hel"
```

## Comparaison avec les N-grammes de bord (Edge N-grams)

Certains moteurs de recherche prennent en charge les "N-grammes de bord"
(uniquement la génération de N-grammes à partir du début des mots).
C'est plus efficace en espace pour l'autocomplétion :

- N-grammes complets : "hello" → "he", "el", "ll", "lo", "hel", "ell", ...
- N-grammes de bord : "hello" → "h", "he", "hel", "hell", "hello"

Le `NgramTokenizer` de Whoosh génère des N-grammes complets (bidirectionnels).
Pour un comportement similaire aux N-grammes de bord, utilisez les
paramètres `minsize` et `maxsize` stratégiquement, ou utilisez des
requêtes `Prefix` sur un champ tokenisé standard.

## Considérations de performance

- Les index N-gramme sont généralement beaucoup plus volumineux que les
  index standard.
- Chaque jeton original produit plusieurs jetons N-gramme, augmentant
  la taille de l'index.
- Choisissez `minsize` et `maxsize` avec soin pour équilibrer la qualité
  de recherche et la taille de l'index.
- Pour l'autocomplétion, envisenez d'utiliser des requêtes `Prefix` sur
  un champ non-N-gramme pour de meilleures performances.
