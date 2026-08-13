---
title: "Analyseurs"
sidebar_position: 6
Module: whoosh.analysis
Version: 2.7.4
---

:::info
Suite au renommage de `whoosh-reloaded` en `whoosh-ng`, les nouveaux modules spécifiques à Whoosh-NG se trouvent généralement sous `whoosh_modern`.
Les composants Whoosh core (comme `whoosh.analysis`, `whoosh.index`) restent accessibles directement sous l'espace de noms `whoosh` pour la rétrocompatibilité.
:::

# Analyseurs

## Overview

Un analyseur est une fonction ou une classe callable (une classe avec une méthode `__call__`) qui prend une chaîne unicode et retourne un générateur de tokens. En général, un "token" est un mot, par exemple la chaîne "Mary had a little lamb" peut produire les tokens "Mary", "had", "a", "little", et "lamb". Cependant, les tokens ne sont pas toujours des mots ; cela dépend de l'analyseur utilisé.

## Tokenizers

Un tokenizer est un type d'analyseur qui divise une chaîne de caractères en tokens.

Par exemple, la classe `whoosh.analysis.RegexTokenizer` implémente une expression régulière pour diviser le texte en tokens :

```python
from whoosh.analysis import RegexTokenizer

tokenizer = RegexTokenizer()
for token in tokenizer("Hello there my friend!"):
    print(repr(token.text))
# u'Hello'
# u'there'
# u'my'
# u'friend'
```

## Filtres

Un filtre est un callable qui prend un générateur de Tokens (soit un tokenizer, soit un autre filtre) et retourne à son tour une série de Tokens.

Par exemple, le `whoosh.analysis.LowercaseFilter()` fourni filtre les tokens en convertissant leur texte en minuscules. L'implémentation est très simple :

```python
def LowercaseFilter(tokens):
    """Utilise lower() pour mettre le texte des tokens en minuscules."""
    for t in tokens:
        t.text = t.text.lower()
        yield t
```

Vous pouvez envelopper le filtre autour d'un tokenizer pour le voir en action :

```python
from whoosh.analysis import LowercaseFilter, RegexTokenizer

tokenizer = RegexTokenizer()
for token in LowercaseFilter(tokenizer("These ARE the things I want!")):
    print(repr(token.text))
# u'these'
# u'are'
# u'the'
# u'things'
# u'i'
# u'want'
```

## Analyseurs

Un analyseur est simplement un moyen de combiner un tokenizer et quelques filtres en un seul package.

Vous pouvez implémenter un analyseur comme une classe ou fonction personnalisée, ou composer des tokenizers et filtres en utilisant le caractère `|` :

```python
my_analyzer = RegexTokenizer() | LowercaseFilter() | StopFilter()
```

## Voir aussi

- [API: analysis](../api/analysis) — Référence complète pour les analyseurs, tokenizers et filtres
