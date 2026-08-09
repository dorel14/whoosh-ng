---
title: "Fournisseurs d'Autocomplétion"
sidebar_position: 54
---

# Fournisseurs d'Autocomplétion

Module: `whoosh_modern.autocomplete`
Version: 2.0.0

Le module d'autocomplétion fournit plusieurs stratégies de fournisseurs pour la suggestion de requêtes et la recherche en tapant. Tous les fournisseurs implémentent une interface commune afin de pouvoir changer de stratégie à l'exécution. Les fournisseurs sont enregistrés via le `AutocompleteRegistry` et chargés via des entry points.

## Vue d'ensemble du module

```text
whoosh_modern.autocomplete
    ├── provider.py   # AutocompleteHit, AutocompleteProvider (Protocole)
    ├── ngram.py      # NGramProvider (basé sur des n-grammes de caractères)
    ├── edge_ngram.py # InvertedIndexAutocomplete (correspondance de préfixe par indice inversé)
    ├── fuzzy.py      # FuzzySuggestProvider (correspondance approximative via rapidfuzz)
    ├── factory.py    # create_autocomplete()
    └── plugin.py     # AutocompletePlugin (plugin via entry point)
```

## AutocompleteProvider (Classe de Base)

Située dans `whoosh_modern.autocomplete.provider` :

```python
from whoosh_modern.autocomplete.provider import AutocompleteProvider, AutocompleteHit

class MyProvider(AutocompleteProvider):
    def add(self, phrases: Iterable[str]) -> None:
        """Ajouter des phrases à l'index du fournisseur."""
        ...

    def search(self, prefix: str, limit: int = 10) -> list[AutocompleteHit]:
        """Retourner les suggestions d'autocomplétion pour le préfixe donné."""
        ...
```

### AutocompleteHit

Un objet de résultat simple retourné par les fournisseurs :

```python
class AutocompleteHit:
    def __init__(self, text: str, score: float) -> None:
        self.text = text    # La phrase correspondante
        self.score = score  # Score de pertinence (plus haut = mieux)
```

## Fournisseurs Intégrés

### InvertedIndexAutocomplete

Situé dans `whoosh_modern.autocomplete.edge_ngram`. Utilise une correspondance simple de préfixe contre une liste en mémoire :

```python
from whoosh_modern.autocomplete.edge_ngram import InvertedIndexAutocomplete

provider = InvertedIndexAutocomplete()
provider.add(["python", "pyramid", "pytorch", "java", "javascript"])

hits = provider.search("py", limit=5)
for hit in hits:
    print(f"{hit.text} (score: {hit.score})")
# Output:
# python (score: 0.45)
# pyramid (score: 0.43)
# pytorch (score: 0.43)
```

**Score** : Les correspondances exactes de préfixe obtiennent un bonus de 1.5x ; le score de base est `1.0 / (len(phrase) + 1)`.

### NGramProvider

Situé dans `whoosh_modern.autocomplete.ngram`. Construit un index de n-grammes de caractères pour une correspondance de sous-chaîne souple :

```python
from whoosh_modern.autocomplete.ngram import NGramProvider

provider = NGramProvider(n=3)
provider.add(["python programming", "java development", "rust language"])

hits = provider.search("pyt", limit=5)
for hit in hits:
    print(f"{hit.text} (score: {hit.score})")
```

**Paramètres :**

| Paramètre | Type | Défaut | Description                          |
|-----------|------|---------|--------------------------------------|
| `n`       | `int` | `3`     | Taille des n-grammes de caractères   |

**Fonctionnement** : Les n-grammes sont extraits de chaque phrase (en minuscules). Lors de la recherche, les n-grammes du préfixe sont comparés à l'index. Les phrases avec plus de n-grammes correspondants obtiennent des scores plus élevés.

### FuzzySuggestProvider

Situé dans `whoosh_modern.autocomplete.fuzzy`. Utilise `rapidfuzz` pour une correspondance approximative (fautes de frappe, correspondances partielles) :

```python
from whoosh_modern.autocomplete.fuzzy import FuzzySuggestProvider

# Nécessite: pip install whoosh-ng[fuzzy]
provider = FuzzySuggestProvider(max_distance=2, score_cutoff=50.0)
provider.add(["python", "pyramid", "pytorch", "java", "javascript"])

hits = provider.search("pythn", limit=5)  # Faute de frappe dans "python"
for hit in hits:
    print(f"{hit.text} (score: {hit.score})")
# Output: python (score: 0.95), ...
```

**Paramètres :**

| Paramètre       | Type  | Défaut  | Description                              |
|-----------------|-------|----------|------------------------------------------|
| `max_distance`  | `int` | `2`      | Distance d'édition maximale (réservé pour une utilisation future) |
| `score_cutoff`  | `float` | `50.0` | Score de similarité minimum (échelle 0-100)   |

**Note** : Nécessite `rapidfuzz` (`pip install whoosh-ng[fuzzy]`). Retourne `ImportError` si non installé.

## Fonction d'Usine

Située dans `whoosh_modern.autocomplete.factory` :

```python
from whoosh_modern.autocomplete import create_autocomplete

# Créer n'importe quel fournisseur par nom
provider = create_autocomplete("inverted")   # InvertedIndexAutocomplete
provider = create_autocomplete("ngram", n=3) # NGramProvider avec n personnalisé
provider = create_autocomplete("fuzzy", max_distance=2, score_cutoff=60.0)
```

**Fournisseurs disponibles :**

| Nom         | Classe                    | Dépendance Optionnelle |
|-------------|---------------------------|------------------------|
| `"inverted"`| `InvertedIndexAutocomplete` | Aucune               |
| `"ngram"`   | `NGramProvider`           | Aucune                |
| `"fuzzy"`   | `FuzzySuggestProvider`    | `rapidfuzz`           |

## Enregistrement dans AutocompleteRegistry

Les fournisseurs sont enregistrés dans `whoosh.registry.AutocompleteRegistry` (une instance de `Registry`) :

```python
from whoosh.registry import AutocompleteRegistry
from whoosh_modern.autocomplete import create_autocomplete

# Enregistrer un fournisseur
provider = create_autocomplete("ngram", n=3)
AutocompleteRegistry.register("ngram-suggester", provider, owner="my_app")

# Le récupérer plus tard
suggester = AutocompleteRegistry.get("ngram-suggester")

# Lister tous les fournisseurs enregistrés
print(AutocompleteRegistry.list_keys())
```

## AutocompletePlugin (Entry Point)

Situé dans `whoosh_modern.autocomplete.plugin`, c'est le plugin intégré enregistré via le groupe d'entry points `whoosh_ng.plugins` :

```python
from whoosh_modern.autocomplete.plugin import AutocompletePlugin

# Automatiquement chargé par PluginManager.load_plugins()
# Enregistre le fournisseur "inverted" dans AutocompleteRegistry
```

### Déclaration d'Entry Point

Dans `pyproject.toml` :

```toml
[project.entry-points."whoosh_ng.plugins"]
whoosh_autocomplete = "whoosh_modern.autocomplete.plugin:AutocompletePlugin"
```

### Détails du Plugin

```python
class AutocompletePlugin(Plugin):
    name = "whoosh_autocomplete"
    version = "3.0.0"

    def register(self, manager):
        # Enregistre InvertedIndexAutocomplete comme "inverted"
        AutocompleteRegistry.register(
            "inverted", create_autocomplete("inverted"), self.name
        )

    def register_hooks(self):
        # Enregistre un hook on_search (actuellement un no-op)
        from whoosh.hooks import hookimpl, register_hook
        register_hook("on_search", hookimpl(on_search))
```

## Exemples d'Utilisation

### Utilisation de Base

```python
from whoosh_modern.autocomplete import create_autocomplete

# Créer et peupler un fournisseur
provider = create_autocomplete("inverted")
provider.add([
    "python programming",
    "python tutorial",
    "java tutorial",
    "javascript framework",
])

# Rechercher des suggestions
hits = provider.search("py", limit=3)
for hit in hits:
    print(f"{hit.text}: {hit.score:.3f}")
```

### Correspondance Floue avec Tolérance aux Fautes

```python
from whoosh_modern.autocomplete import create_autocomplete

provider = create_autocomplete("fuzzy", score_cutoff=70.0)
provider.add(["python", "pytorch", "tensorflow", "keras"])

# Même avec une faute, les suggestions pertinentes sont retournées
hits = provider.search("pyton", limit=5)
for hit in hits:
    print(hit.text, hit.score)
```

### Correspondance par N-grammes pour les Mots Partiels

```python
from whoosh_modern.autocomplete import create_autocomplete

# Utiliser des n-grammes de taille 3 pour une meilleure correspondance de sous-chaînes
provider = create_autocomplete("ngram", n=3)
provider.add(["machine learning", "deep learning", "neural networks"])

# Trouve les phrases contenant les n-grammes de "machin"
hits = provider.search("machin", limit=5)
```

### Intégration avec la Recherche

```python
from whoosh_modern.autocomplete import create_autocomplete

# Construire le fournisseur d'autocomplétion
provider = create_autocomplete("inverted")
provider.add(["python", "java", "javascript", "go", "rust"])

# Utiliser dans un endpoint de recherche
def suggest(prefix: str, limit: int = 5):
    hits = provider.search(prefix, limit=limit)
    return [{"text": h.text, "score": h.score} for h in hits]

# Dans votre endpoint FastAPI/REST :
# GET /api/suggest?q=py&limit=5
# Response: [{"text": "python", "score": 0.45}, ...]
```

## Comparaison des Fournisseurs

| Fournisseur              | Correspondance       | Forces                    | Faiblesses                | Dépendance    |
|--------------------------|----------------------|---------------------------|---------------------------|---------------|
| `inverted`               | Préfixe              | Simple, rapide, pas de deps | Pas de tolérance aux fautes | Aucune          |
| `ngram`                  | Chevauchement n-gramme | Correspondance de sous-chaînes, flexible | Plus lent que préfixe     | Aucune        |
| `fuzzy`                  | Distance d'édition   | Tolérance aux fautes, flexible | Nécessite rapidfuzz    | `rapidfuzz`   |

## Installation

```bash
# Autocomplétion core (inverted + n-gram)
pip install whoosh-ng

# Avec correspondance floue
pip install whoosh-ng[fuzzy]

# Analyse moderne complète
pip install whoosh-ng[modern]
```

## Voir Aussi

- [Guide Système de Plugins](plugins-avances.md) — Enregistrement et découverte de plugins
- [Guide Middleware](middleware-pipeline.md) — Intégration du pipeline de middleware
- [Intégration des Providers](provider-integration.md) — Guide complet du pipeline pour tous les providers
- [API: Moderne](../api/modern.md) — Référence complète de l'API pour les extensions d'autocomplétion
