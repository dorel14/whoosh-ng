---
title: 'Racinement (Stemming) et mots vides'
sidebar_position: 100
---

# Racinement (Stemming) et mots vides

Ce guide couvre l'utilisation des racines (stemmers), des filtres de
mots vides (stop words) et de l'analyse de texte spécifique à chaque
langue avec Whoosh.

## Racines (Stemmers)

Un racine (stemmer) réduit les mots à leur forme racine (par ex.,
"running" → "run", "cats" → "cat"), afin que les différentes formes
du même mot correspondent lors des recherches.

### Utilisation de StemmerFilter

```python
from whoosh.analysis import RegexTokenizer, StemmerFilter
from whoosh.lang.porter import stem
from whoosh import fields

# English Porter stemmer
stem_analyzer = RegexTokenizer() | StemmerFilter(stemfn=stem)

schema = fields.Schema(
    title=fields.TEXT(stored=True),
    content=fields.TEXT(analyzer=stem_analyzer),
)
```

### Racines Snowball

Whoosh inclut des racines Snowball pour plusieurs langues :

```python
from whoosh.analysis import StemmerFilter
from whoosh.lang.snowball import EnglishStemmer

stem_analyzer = RegexTokenizer() | StemmerFilter(stemfn=EnglishStemmer().stem)
```

### Sélection de racine selon la langue

```python
from whoosh.lang import stemmer_for_language, StemmerFilter
from whoosh.analysis import RegexTokenizer

stem = stemmer_for_language("en")
analyzer = RegexTokenizer() | StemmerFilter(stemfn=stem)

# Ou utilisez l'analyseur StemmingAnalyzer :
from whoosh.analysis import StemmingAnalyzer

analyzer = StemmingAnalyzer("en")
```

### Langues disponibles

```python
from whoosh.lang import languages, has_stemmer, has_stopwords

print(languages)  # ('ar', 'da', 'nl', 'en', 'fi', 'fr', ...)
print(has_stemmer("en"))  # True
print(has_stopwords("en"))  # True
```

## Mots vides (Stop Words)

Les mots vides sont des mots fréquents (comme "the", "a", "and") qui
sont généralement filtrés lors de l'indexation car ils apparaissent
dans trop de documents pour être utiles au classement.

### Utilisation de StopFilter

```python
from whoosh.analysis import RegexTokenizer, StopFilter
from whoosh.lang import stopwords_for_language

# English stop words
stop_words = set(stopwords_for_language("en"))
stop_analyzer = RegexTokenizer() | StopFilter(stoplist=stop_words)

schema = fields.Schema(
    content=fields.TEXT(analyzer=stop_analyzer),
)
```

### Combinaison de racinement et de mots vides

```python
from whoosh.analysis import StemmingAnalyzer

# StemmingAnalyzer charge automatiquement le racine et les mots vides pour la langue
analyzer = StemmingAnalyzer("en")

schema = fields.Schema(
    content=fields.TEXT(analyzer=analyzer),
)
```

### Mots vides personnalisés

```python
from whoosh.analysis import RegexTokenizer, StopFilter

# Liste personnalisée de mots vides
custom_stops = frozenset(["the", "a", "an", "foo", "bar"])
analyzer = RegexTokenizer() | StopFilter(stoplist=custom_stops)
```

## StemmingAnalyzer (Recommandé)

Le `StemmingAnalyzer` combine le tokeniseur, le racinement et le
filtrage des mots vides :

```python
from whoosh.analysis import StemmingAnalyzer

# Utilise automatiquement le bon racine et les mots vides pour la langue
analyzer = StemmingAnalyzer("en")

# Vous pouvez remplacer les valeurs par défaut
analyzer = StemmingAnalyzer("en",
                            use_stopwords=True,
                            use_stems=True)
```

### Options de StemmingAnalyzer

- `lang` : Code de langue (ex. : `"en"`, `"fr"`, `"de"`)
- `use_stopwords` : Charge et applique les mots vides (par défaut `True`)
- `use_stems` : Applique le racinement (par défaut `True`)
- `args` : Arguments passés au tokeniseur
- `kwargs` : Arguments du mot-clé pour le racine ou les mots vides

## Considérations spécifiques selon la langue

### Arabe (ISRI Stemmer)

```python
from whoosh.analysis import StemmerFilter
from whoosh.lang.isri import ISRIStemmer

stem_analyzer = RegexTokenizer() | StemmerFilter(stemfn=ISRIStemmer().stem)
```

### Double Métaphone pour la correspondance phonétique

```python
from whoosh.analysis import RegexTokenizer, DoubleMetaphoneFilter

analyzer = RegexTokenizer() | DoubleMetaphoneFilter()
```

## Racinement côté requête

L'analyseur est appliqué à la fois lors de l'indexation et lors de la
requête (via l'analyseur de requête), donc le racinement est automatiquement
appliqué aux termes de recherche :

```python
from whoosh.qparser import QueryParser

# Si l'index utilise le racinement, les requêtes sont racinées aussi
qp = QueryParser("content", schema=ix.schema)
q = qp.parse("running cats")  # Correspondra à "run", "cat", etc.
```

## Analyse N-gramme

Pour la correspondance de sous-chaînes et les requêtes par préfixe,
utilisez les analyseurs N-gramme :

```python
from whoosh.analysis import NgramWordAnalyzer

analyzer = NgramWordAnalyzer(minsize=2, maxsize=4)
schema = fields.Schema(content=fields.TEXT(analyzer=analyzer))
```

Voir le [Guide N-grammes](ngrams.md) pour plus de détails.

## Fournisseurs de racines modernes (Whoosh-NG 2.0)

Whoosh-NG 2.0 introduit un système de fournisseurs de racines de style
plugin avec détection automatique, support de PyStemmer et d'analyseurs
spécifiques à chaque langue. Pour plus de détails, voir le
[Guide des fournisseurs de racines](stemming-sprint-d.md).
