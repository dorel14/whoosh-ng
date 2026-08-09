---
title: 'Language Support API'
sidebar_position: 0
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
> Le contenu anglais est affiché ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->


# Language Support API

Language detection helpers, stemmer selection, stop-word lists, and
language-specific modules (Snowball stemmers, ISRI stemmer, Soundex,
Double Metaphone, etc.).

## Module Overview

The `whoosh.lang` package provides functions for detecting and selecting
language-specific resources (stemmers, stop words) and submodules containing
stemmers for various languages.

## Supported Languages

```python
whoosh.lang.languages = ("ar", "da", "nl", "en", "fi", "fr", "de", "hu",
                         "it", "no", "pt", "ro", "ru", "es", "sv", "tr")
```

Two-letter ISO 639-1 language codes for which stemmers or stop-word lists
are available.

## Language Aliases

```python
whoosh.lang.aliases = { ... }
```

A dictionary mapping alternate language identifiers to their canonical
two-letter codes. Includes ISO 639-3 three-letter codes, English names,
and native-language names.

## Exceptions

### `NoStemmer`

```python
class whoosh.lang.NoStemmer
```

Raised by `stemmer_for_language()` when no stemmer is available for the
given language.

### `NoStopWords`

```python
class whoosh.lang.NoStopWords
```

Raised by `stopwords_for_language()` when no stop-word list is available for
the given language.

## Language Functions

### `two_letter_code`

```python
whoosh.lang.two_letter_code(name) -> str or None
```

Converts a language identifier to its canonical two-letter code. Accepts
two-letter codes, ISO 639-3 codes, English names, and native-language names.

```python
from whoosh.lang import two_letter_code

code = two_letter_code("french")   # 'fr'
code = two_letter_code("deutsch")  # 'de'
code = two_letter_code("español")  # 'es'
```

### `has_stemmer`

```python
whoosh.lang.has_stemmer(lang) -> bool
```

Returns `True` if a stemmer is available for the given language.

### `has_stopwords`

```python
whoosh.lang.has_stopwords(lang) -> bool
```

Returns `True` if a stop-word list is available for the given language.

### `stemmer_for_language`

```python
whoosh.lang.stemmer_for_language(lang) -> callable
```

Returns a stemmer function for the given language. Raises `NoStemmer` if
no stemmer is available.

**Supported languages and stemmers:**
- `"en"` / `"en_porter"`: Original Porter stemmer (`whoosh.lang.porter`)
- `"ar"`: ISRI Arabic stemmer (`whoosh.lang.isri`)
- `"da"`: Danish Snowball stemmer
- `"nl"`: Dutch Snowball stemmer
- `"en"`: English Snowball stemmer
- `"fi"`: Finnish Snowball stemmer
- `"fr"`: French Snowball stemmer
- `"de"`: German Snowball stemmer
- `"hu"`: Hungarian Snowball stemmer
- `"it"`: Italian Snowball stemmer
- `"no"`: Norwegian Snowball stemmer
- `"pt"`: Portuguese Snowball stemmer
- `"ro"`: (no stemmer currently)
- `"ru"`: Russian Snowball stemmer
- `"es"`: Spanish Snowball stemmer
- `"sv"`: Swedish Snowball stemmer
- `"tr"`: (no stemmer currently)

```python
from whoosh.lang import stemmer_for_language

stem = stemmer_for_language("en")
print(stem("running"))  # 'run'
```

### `stopwords_for_language`

```python
whoosh.lang.stopwords_for_language(lang) -> list
```

Returns the stop-word list for the given language. Raises `NoStopWords` if
no stop-word list is available.

```python
from whoosh.lang import stopwords_for_language

stops = stopwords_for_language("en")
```

## Snowball Stemmers

The `whoosh.lang.snowball` subpackage contains stemmers implementing the
Snowball stemming algorithms for various languages.

### Available Stemmers

| Module | Class | Language |
|--------|-------|----------|
| `snowball.english` | `EnglishStemmer` | English |
| `snowball.dutch` | `DutchStemmer` | Dutch |
| `snowball.finnish` | `FinnishStemmer` | Finnish |
| `snowball.french` | `FrenchStemmer` | French |
| `snowball.german` | `GermanStemmer` | German |
| `snowball.hungarian` | `HungarianStemmer` | Hungarian |
| `snowball.italian` | `ItalianStemmer` | Italian |
| `snowball.norwegian` | `NorwegianStemmer` | Norwegian |
| `snowball.portugese` | `PortugueseStemmer` | Portuguese |
| `snowball.russian` | `RussianStemmer` | Russian |
| `snowball.romanian` | `RomanianStemmer` | Romanian |
| `snowball.spanish` | `SpanishStemmer` | Spanish |
| `snowball.swedish` | `SwedishStemmer` | Swedish |
| `snowball.danish` | `DanishStemmer` | Danish |

### Base Classes

```python
class whoosh.lang.snowball.bases._ScandinavianStemmer
class whoosh.lang.snowball.bases._StandardStemmer
```

Internal base classes for Snowball stemmers. User code should use the
language-specific stemmer classes directly.

### `classes`

```python
whoosh.lang.snowball.classes = {"da": DanishStemmer, "nl": DutchStemmer, ...}
```

Dictionary mapping two-letter language codes to Snowball stemmer classes.

## Porter Stemmer

### `whoosh.lang.porter`

The original Porter stemming algorithm, faster but less accurate than
Snowball English stemmer.

#### `stem`

```python
whoosh.lang.porter.stem(w) -> str
```

Stems a single English word using the Porter algorithm.

## ISRI Stemmer

### `whoosh.lang.isri.ISRIStemmer`

```python
class whoosh.lang.isri.ISRIStemmer
```

Arabic stemmer based on the Information Science Research Institute (ISRI)
algorithm. Does not use a root dictionary.

#### `stem`

```python
def ISRIStemmer.stem(word) -> str
```

Stems an Arabic word.

## Double Metaphone

### `whoosh.lang.dmetaphone.double_metaphone`

```python
whoosh.lang.dmetaphone.double_metaphone(text) -> tuple
```

Returns a tuple of `(primary, secondary)` metaphone codes for the given
text, using the Double Metaphone algorithm.

## Soundex

### `whoosh.lang.phonetic`

Soundex implementations for phonetic matching.

#### `soundex_en`

```python
whoosh.lang.phonetic.soundex_en(word) -> str
```

English Soundex encoding.

#### `soundex_esp`

```python
whoosh.lang.phonetic.soundex_esp(word) -> str
```

Spanish Soundex encoding.

#### `soundex_ar`

```python
whoosh.lang.phonetic.soundex_ar(word) -> str
```

Arabic Soundex encoding.

## WordNet Thesaurus

### `whoosh.lang.wordnet.Thesaurus`

```python
class whoosh.lang.wordnet.Thesaurus
```

Provides synonym expansion based on WordNet-style data.

**Methods:**
- `synonyms(word)`: Returns the set of synonyms for `word`.
- `__contains__(word)`: Returns `True` if `word` is in the thesaurus.

### Functions

```python
whoosh.lang.wordnet.parse_file(f) -> dict
whoosh.lang.wordnet.make_index(storage, indexname, word2nums, num2words)
whoosh.lang.wordnet.synonyms(word2nums, num2words, word) -> set
```

## Lovins Stemmer

### `whoosh.lang.lovins`

A suffix-stripping stemmer by Lovins. Functions include:
- `stem(word)`: Main stemming function.
- `remove_ending(word)`: Removes suffixes.
- `fix_ending(word)`: Fixes the word ending after stemming.

## Paice-Husk Stemmer

### `whoosh.lang.paicehusk.PaiceHuskStemmer`

```python
class whoosh.lang.paicehusk.PaiceHuskStemmer(rules)
```

A rule-based stemmer using Paice-Husk rules.

#### `stem`

```python
def PaiceHuskStemmer.stem(word) -> str
```

Stems a word using the Paice-Husk algorithm.

**Usage note:** The module also exposes a pre-configured stemmer:
```python
whoosh.lang.paicehusk.stem = PaiceHuskStemmer(defaultrules).stem
```
