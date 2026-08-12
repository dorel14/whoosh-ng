---
title: "Providers d'Autocomplétion"
sidebar_position: 54
---

# Providers d'Autocomplétion

Module : `whoosh_modern.autocomplete`
Version : 2.0.0

Le module d'autocomplétion fournit plusieurs stratégies de provider pour les
suggestions de requêtes et la recherche en taper-à-mesure (type-ahead). Tous
les providers implémentent une interface commune afin que vous puissiez
intervertir les stratégies à l'exécution. Les providers sont enregistrés via
l'`AutocompleteRegistry` et chargés par points d'entrée.

## Aperçu du module

```text
whoosh_modern.autocomplete
    ├── provider.py   # AutocompleteHit, AutocompleteProvider (Protocole)
    ├── ngram.py      # NGramProvider (basé sur les n-grammes de caractères)
    ├── edge_ngram.py # InvertedIndexAutocomplete (correspondance de préfixe par index inversé)
    ├── fuzzy.py      # FuzzySuggestProvider (correspondance approximative via rapidfuzz)
    ├── factory.py    # factory create_autocomplete()
    └── plugin.py     # AutocompletePlugin (plugin de point d'entrée)
```

## AutocompleteProvider (classe de base)

Localisé dans `whoosh_modern.autocomplete.provider` :

```python
from whoosh_modern.autocomplete.provider import AutocompleteProvider, AutocompleteHit

class MyProvider(AutocompleteProvider):
    def add(self, phrases: Iterable[str]) -> None:
        """Ajoute des phrases à l'index du provider."""
        ...

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
        """Renvoie les suggestions d'autocomplétion pour le préfixe donné."""
        ...
```

### AutocompleteHit

Un objet résultat simple renvoyé par les providers :

```python
class AutocompleteHit:
    def __init__(self, text: str, score: float) -> None:
        self.text = text    # La phrase correspondante
        self.score = score  # Score de pertinence (plus élevé = meilleur)
```

## Providers intégrés

### InvertedIndexAutocomplete

Localisé dans `whoosh_modern.autocomplete.edge_ngram`. Utilise une
correspondance de préfixe simple contre une liste en mémoire :

```python
from whoosh_modern.autocomplete.edge_ngram import InvertedIndexAutocomplete

provider = InvertedIndexAutocomplete()
provider.add(["python", "pyramid", "pytorch", "java", "javascript"])

hits = provider.search("py", limit=5)
for hit in hits:
    print(f"{hit.text} (score: {hit.score})")
# Sortie :
# python (score: 0.45)
# pyramid (score: 0.43)
# pytorch (score: 0.43)
```

**Scoring** : les correspondances de préfixe exactes reçoivent un bonus 1.5x ;
le score de base est `1.0 / (len(phrase) + 1)`.

### NGramProvider

Localisé dans `whoosh_modern.autocomplete.ngram`. Construit un index de
n-grammes de caractères pour la correspondance approximative de sous-chaînes :

```python
from whoosh_modern.autocomplete.ngram import NGramProvider

provider = NGramProvider(n=3)
provider.add(["python programming", "java development", "rust language"])

hits = provider.search("pyt", limit=5)
for hit in hits:
    print(f"{hit.text} (score: {hit.score})")
```

**Paramètres :**

| Paramètre | Type | Défaut | Description                  |
|-----------|------|--------|------------------------------|
| `n`       | `int` | `3`    | Taille des n-grammes de caractères |

**Fonctionnement** : les n-grammes sont extraits de chaque phrase (en
minuscules). Lors de la recherche, les n-grammes du préfixe sont appariés avec
l'index. Les phrases avec le plus de n-grammes correspondants reçoivent les
scores les plus élevés.

### FuzzySuggestProvider

Localisé dans `whoosh_modern.autocomplete.fuzzy`. Utilise `rapidfuzz` pour la
correspondance approximative de chaînes (fautes de frappe, correspondances
partielles) :

```python
from whoosh_modern.autocomplete.fuzzy import FuzzySuggestProvider

# Nécessite : pip install whoosh-ng[fuzzy]
provider = FuzzySuggestProvider(max_distance=2, score_cutoff=50.0)
provider.add(["python", "pyramid", "pytorch", "java", "javascript"])

hits = provider.search("pythn", limit=5)  # Faute de frappe dans "python"
for hit in hits:
    print(f"{hit.text} (score: {hit.score})")
# Sortie : python (score: 0.95), ...
```

**Paramètres :**

| Paramètre       | Type  | Défaut  | Description                              |
|-----------------|-------|---------|------------------------------------------|
| `max_distance`  | `int` | `2`     | Distance d'édition max (non utilisé directement par rapidfuzz, réservé) |
| `score_cutoff`  | `float` | `50.0` | Score de similarité minimum (échelle 0-100) |

**Note** : nécessite `rapidfuzz` (`pip install whoosh-ng[fuzzy]`). Lève
`ImportError` si non installé.

## Fonction factory

Localisée dans `whoosh_modern.autocomplete.factory` :

```python
from whoosh_modern.autocomplete import create_autocomplete

# Crée n'importe quel provider par nom
provider = create_autocomplete("inverted")   # InvertedIndexAutocomplete
provider = create_autocomplete("ngram", n=3) # NGramProvider avec n personnalisé
provider = create_autocomplete("fuzzy", max_distance=2, score_cutoff=60.0)
```

**Providers disponibles :**

| Nom        | Classe                    | Dépendance optionnelle |
|------------|---------------------------|------------------------|
| `"inverted"`| `InvertedIndexAutocomplete` | Aucune              |
| `"ngram"`   | `NGramProvider`          | Aucune                |
| `"fuzzy"`   | `FuzzySuggestProvider`   | `rapidfuzz`           |

## Enregistrement dans l'AutocompleteRegistry

Les providers sont enregistrés dans `whoosh.registry.AutocompleteRegistry`
(une instance `Registry`) :

```python
from whoosh.registry import AutocompleteRegistry
from whoosh_modern.autocomplete import create_autocomplete

# Enregistre un provider
provider = create_autocomplete("ngram", n=3)
AutocompleteRegistry.register("ngram-suggester", provider, owner="my_app")

# Le récupère plus tard
suggester = AutocompleteRegistry.get("ngram-suggester")

# Liste tous les providers enregistrés
print(AutocompleteRegistry.list_keys())
```

## AutocompletePlugin (point d'entrée)

Localisé dans `whoosh_modern.autocomplete.plugin`, c'est le plugin intégré
enregistré via le groupe de points d'entrée `whoosh_ng.plugins` :

```python
from whoosh_modern.autocomplete.plugin import AutocompletePlugin

# Chargé automatiquement par PluginManager.load_plugins()
# Enregistre le provider "inverted" dans AutocompleteRegistry
```

### Déclaration du point d'entrée

Dans `pyproject.toml` :

```toml
[project.entry-points."whoosh_ng.plugins"]
whoosh_autocomplete = "whoosh_modern.autocomplete.plugin:AutocompletePlugin"
```

### Détails du plugin

```python
class AutocompletePlugin(Plugin):
    name = "whoosh_autocomplete"
    version = "3.0.0"

    def register(self, manager):
        # Enregistre InvertedIndexAutocomplete en tant que "inverted"
        AutocompleteRegistry.register(
            "inverted", create_autocomplete("inverted"), self.name
        )

    def register_hooks(self):
        # Enregistre un hook on_search (actuellement sans effet)
        from whoosh.hooks import hookimpl, register_hook
        register_hook("on_search", hookimpl(on_search))
```

## Exemples d'utilisation

### Utilisation de base

```python
from whoosh_modern.autocomplete import create_autocomplete

# Crée et remplit un provider
provider = create_autocomplete("inverted")
provider.add([
    "python programming",
    "python tutorial",
    "java tutorial",
    "javascript framework",
])

# Recherche des suggestions
hits = provider.search("py", limit=3)
for hit in hits:
    print(f"{hit.text}: {hit.score:.3f}")
```

### Utilisation de la correspondance floue avec tolérance aux fautes

```python
from whoosh_modern.autocomplete import create_autocomplete

provider = create_autocomplete("fuzzy", score_cutoff=70.0)
provider.add(["python", "pytorch", "tensorflow", "keras"])

# Même avec une faute de frappe, des suggestions pertinentes sont renvoyées
hits = provider.search("pyton", limit=5)
for hit in hits:
    print(hit.text, hit.score)
```

### Utilisation des n-grammes pour les mots partiels

```python
from whoosh_modern.autocomplete import create_autocomplete

# Utilise des 3-grammes pour une meilleure correspondance de sous-chaînes
provider = create_autocomplete("ngram", n=3)
provider.add(["machine learning", "deep learning", "neural networks"])

# Trouve les phrases contenant les n-grammes de "machin"
hits = provider.search("machin", limit=5)
```

### Intégration avec la recherche

```python
from whoosh_modern.autocomplete import create_autocomplete

# Construit le provider d'autocomplétion
provider = create_autocomplete("inverted")
provider is None  # (exemple conceptuel)
provider = create_autocomplete("inverted")
provider.add(["python", "java", "javascript", "go", "rust"])

# Utilise dans un endpoint de recherche
def suggest(prefix: str, limit: int = 5):
    hits = provider.search(prefix, limit=limit)
    return [{"text": h.text, "score": h.score} for h in hits]

# Dans votre endpoint FastAPI/REST :
# GET /api/suggest?q=py&limit=5
# Réponse : [{"text": "python", "score": 0.45}, ...]
```

## Comparaison des providers

| Provider              | Correspondance  | Forces                    | Faiblesses               | Dépendance    |
|-----------------------|----------------|---------------------------|--------------------------|---------------|
| `inverted`            | Préfixe         | Simple, rapide, sans deps | Pas de tolérance aux fautes | Aucune     |
| `ngram`               | Recouvrement n-grammes | Correspondance de sous-chaînes, flexible | Plus lent que le préfixe | Aucune |
| `fuzzy`               | Distance d'édition | Tolérance aux fautes, flexible | Nécessite rapidfuzz | `rapidfuzz` |

## Installation

```bash
# Autocomplétion de base (inverted + n-gram)
pip install whoosh-ng

# Avec correspondance floue
pip install whoosh-ng[fuzzy]

# Analyse moderne complète
pip install whoosh-ng[modern]
```

## Voir aussi

- [Guide du Système de Plugins](plugins-advanced.md) — Enregistrement et découverte de plugins
- [Guide du Middleware](middleware-pipeline.md) — Intégration du pipeline de middleware
- [Guide d'Intégration des Providers](provider-integration.md) — Guide complet du pipeline pour tous les providers
- [API : Linguistique](../api/modern.md) — Référence complète de l'API pour les extensions d'autocomplétion
