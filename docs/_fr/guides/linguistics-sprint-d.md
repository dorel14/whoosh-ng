---
title: "Synonymes & Linguistique"
nav_order: 52
lang: fr
---

# Synonymes & Linguistique

Module: `whoosh_modern.linguistics.synonyms`, `whoosh_modern.linguistics.stemmers`
Version: 2.0.0

Le module de linguistique fournit un moteur complet d'expansion de synonymes et des analyseurs linguistiques spécifiques à chaque langue. Il s'intègre au pipeline de middleware pour étendre les requêtes et les documents avec des synonymes à la fois à l'indexation et au moment de la recherche.

## Vue d'ensemble du module

```text
whoosh_modern.linguistics
    ├── synonyms/
    │   ├── provider.py       # Protocole SynonymProvider + StaticSynonymProvider
    │   ├── yaml_provider.py  # YAMLSynonymProvider
    │   ├── json_provider.py  # JSONSynonymProvider
    │   ├── store.py          # SQLiteSynonymStore
    │   ├── compiler.py       # SynonymCompiler
    │   ├── manager.py        # SynonymManager
    │   ├── middleware.py     # SynonymExpansionMiddleware
    │   └── languages.py      # LANG_SYNONYMS (FR/EN/DE/ES/IT)
    └── stemmers/
        └── __init__.py       # Analyseurs linguistiques (FR/EN/DE/ES/IT)
```

## Fournisseurs de Synonymes

### SynonymProvider (Protocole)

Le protocole de base que tous les fournisseurs de synonymes implémentent :

```python
from whoosh_modern.linguistics.synonyms import SynonymProvider

class MyProvider(SynonymProvider):
    def get_synonyms(self, word: str) -> list[str]:
        """Retourner les synonymes pour le mot donné."""
        ...

    def add_synonym(self, word: str, synonyms: list[str]) -> None:
        """Ajouter des synonymes pour le mot donné."""
        ...

    def remove_synonym(self, word: str, synonym: str) -> None:
        """Supprimer un synonyme pour le mot donné."""
        ...
```

### StaticSynonymProvider

Fournisseur de synonymes en mémoire basé sur un dictionnaire :

```python
from whoosh_modern.linguistics.synonyms import StaticSynonymProvider

provider = StaticSynonymProvider({
    "car": ["automobile", "vehicle", "auto"],
    "house": ["home", "residence"],
})

print(provider.get_synonyms("car"))  # ['automobile', 'vehicle', 'auto']
```

### YAMLSynonymProvider

Charge les synonymes depuis un fichier YAML :

```yaml
# synonyms.yaml
car:
  - automobile
  - vehicle
  - auto
house:
  - home
  - residence
```

```python
from whoosh_modern.linguistics.synonyms import YAMLSynonymProvider

# Nécessite: pip install pyyaml
provider = YAMLSynonymProvider("synonyms.yaml")
print(provider.get_synonyms("car"))  # ['automobile', 'vehicle', 'auto']
```

### JSONSynonymProvider

Charge les synonymes depuis un fichier JSON :

```json
{
    "car": ["automobile", "vehicle", "auto"],
    "house": ["home", "residence"]
}
```

```python
from whoosh_modern.linguistics.synonyms import JSONSynonymProvider

provider = JSONSynonymProvider("synonyms.json")
print(provider.get_synonyms("car"))
```

### SQLiteSynonymStore

Magasin de synonymes persistant basé sur SQLite :

```python
from whoosh_modern.linguistics.synonyms import SQLiteSynonymStore

store = SQLiteSynonymStore("synonyms.db")

# Opérations CRUD
store.add_synonym("car", ["automobile", "vehicle"])
print(store.get_synonyms("car"))  # ['automobile', 'vehicle']
store.remove_synonym("car", "automobile")
print(store.get_synonyms("car"))  # ['vehicle']
store.close()
```

### SynonymCompiler

Précompile les données de synonymes brutes en un format de recherche rapide :

```python
from whoosh_modern.linguistics.synonyms import SynonymCompiler

compiler = SynonymCompiler({"car": ["automobile", "vehicle"]})
compiler.add("house", ["home", "residence"])
compiler.merge({"book": ["publication", "work"]})

compiled = compiler.compile()
print(compiled)
# {'car': ['automobile', 'vehicle'], 'house': ['home', 'residence'], 'book': ['publication', 'work']}
```

## SynonymManager

Le `SynonymManager` est l'interface de haut niveau pour gérer les synonymes. Il encapsule un `StaticSynonymProvider` en interne et prend en charge l'import/export :

```python
from whoosh_modern.linguistics.synonyms import SynonymManager

manager = SynonymManager({"car": ["automobile", "vehicle"]})

# CRUD
manager.add_synonyms("house", ["home", "residence"])
print(manager.get_synonyms("house"))  # ['home', 'residence']
manager.remove_synonym("house", "home")

# Import depuis des sources externes
manager.import_yaml("synonyms.yaml")   # Nécessite PyYAML
manager.import_json("synonyms.json")

# Export
manager.export_json("output.json")
```

### Flux de Travail d'Import/Export

```python
# Import depuis YAML
manager = SynonymManager()
manager.import_yaml("my_synonyms.yaml")

# Export vers JSON (ex: pour migration ou sauvegarde)
manager.export_json("backup.json")
```

## Synonymes Linguistiques Prédéfinis

Le dictionnaire `LANG_SYNONYMS` contient des mappings de synonymes de démarrage pour cinq langues :

```python
from whoosh_modern.linguistics.synonyms import LANG_SYNONYMS

# Langues disponibles : fr, en, de, es, it
french_syns = LANG_SYNONYMS["fr"]
print(french_syns["voiture"])  # ['automobile', 'véhicule']

english_syns = LANG_SYNONYMS["en"]
print(english_syns["car"])  # ['automobile', 'vehicle']

# Initialiser un SynonymManager avec une langue
manager = SynonymManager(LANG_SYNONYMS["fr"])
```

| Langue   | Code | Exemple                               |
|----------|------|---------------------------------------|
| Français | `fr` | `"voiture": ["automobile", "véhicule"]` |
| Anglais  | `en` | `"car": ["automobile", "vehicle"]`    |
| Allemand | `de` | `"auto": ["wagen", "fahrzeug"]`       |
| Espagnol | `es` | `"coche": ["automóvil", "vehículo"]`  |
| Italien  | `it` | `"auto": ["automobile", "veicolo"]`   |

> **Note** : Ce sont des dictionnaires de démarrage minimaux pour la démonstration et les tests. Les déploiements de production devraient charger depuis des sources élaborées ou spécifiques au domaine.

## SynonymExpansionMiddleware

Intègre l'expansion de synonymes dans le pipeline de middleware. Elle étend à la fois les requêtes de recherche et les champs de documents indexés :

```python
from whoosh_modern.linguistics.synonyms import (
    SynonymManager,
    SynonymExpansionMiddleware,
)

# Créer un gestionnaire avec vos synonymes
manager = SynonymManager({
    "car": ["automobile", "vehicle"],
    "house": ["home", "residence"],
})

# Créer le middleware
middleware = SynonymExpansionMiddleware(manager)

# L'enregistrer auprès du PluginManager ou MiddlewareChain
from whoosh.plugins.manager import PluginManager
PluginManager._default.register_middleware("synonym", middleware)
```

### Fonctionnement

- **`before_search`** : Étend `context.query` en ajoutant les synonymes de chaque token
- **`before_index`** : Étend les valeurs de type chaîne dans `context.document` en ajoutant les synonymes

```python
# Avant : query = "car"
# Après :  query = "car automobile vehicle"

# Avant : document = {"title": "house for sale"}
# Après :  document = {"title": "house for sale home residence"}
```

## Analyseurs Linguistiques Spécifiques

Situés dans `whoosh_modern.linguistics.stemmers`, ces analyseurs combinent tokenisation, stemme et suppression des mots vides :

```python
from whoosh_modern.linguistics.stemmers import (
    EnglishAnalyzer,
    FrenchAnalyzer,
    GermanAnalyzer,
    SpanishAnalyzer,
    ItalianAnalyzer,
)

# Chaque analyseur est appelable et retourne une liste de tokens
analyzer = EnglishAnalyzer()
tokens = analyzer("The running cats")
# tokens sont stemmés: ["run", "cat"] (mots vides supprimés)
```

## Voir Aussi

- [Guide Stemmers](stemming-sprint-d.md) — Fournisseurs de stemmers et analyseurs linguistiques
- [Guide Middleware](middleware-sprint-c.md) — Intégration du pipeline de middleware
- [API: Linguistique](../api/modern.md) — Référence complète de l'API
