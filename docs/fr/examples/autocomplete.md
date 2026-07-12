---
color_scheme: dark
title: "Autocomplétion"
parent: "Exemples"
nav_order: 3
lang: fr
---

# Autocomplétion avec Whoosh‑NG

Cet exemple démontre la fonctionnalité **autocomplete/suggestion** avec le plugin `whoosh_modern.autocomplete`.

## 1. Installation

```bash
pip install "whoosh-ng[autocomplete]"
```

## 2. Schéma avec champ Keyword pour les termes

```python
from whoosh import index
from whoosh.fields import Schema, TEXT, KEYWORD
from whoosh_modern.autocomplete.plugin import AutocompletePlugin
from whoosh.plugins.manager import PluginManager

schema = Schema(
    title=TEXT(stored=True),
    tags=KEYWORD(stored=True, commas=True),
)

ix = index.create_in("autocomplete_index", schema)
```

## 3. Enregistrer le plugin

```python
AutocompletePlugin().register(PluginManager())
```

## 4. Indexer les documents

```python
with ix.writer() as w:
    w.add_document(title="Python Programming", tags="python,programming,language")
    w.add_document(title="JavaScript Basics", tags="javascript,programming,web")
    w.add_document(title="Machine Learning", tags="ml,ai,data-science")
    w.commit()
```

## 5. Utiliser l’index inversé pour les suggestions

```python
from whoosh_modern.autocomplete.factory import create_autocomplete
from whoosh.registry import AutocompleteRegistry

provider = AutocompleteRegistry.get("inverted")

with ix.searcher() as s:
    for term in s.lexicon("tags"):
        provider.add_term(term, s.doc_count_all())

suggestions = provider.suggest("py", maxdist=1, limit=5)
print(suggestions)  # ['python', 'programming']
```

## Points clés

- Installez avec `pip install whoosh-ng[autocomplete]`.
- Utilisez des champs `KEYWORD` pour les tags/mots-clés.
- Enregistrez `AutocompletePlugin` pour activer les suggestions.
- Le provider inverted supporte les correspondances floues (`maxdist`).