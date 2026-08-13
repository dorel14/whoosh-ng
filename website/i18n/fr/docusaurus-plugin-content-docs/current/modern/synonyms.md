---
title: "Synonymes"
sidebar_position: 51
---

# Synonymes

Module: `whoosh_modern.linguistics.synonyms`
Version: 3.0.0

Le moteur de synonymes fournit une expansion de synonymes au moment de la requête et de l'indexation via un système de providers pluggables. Il supporte les mappings statiques en mémoire, les fichiers YAML/JSON, la persistance SQLite, et les dictionnaires Wiktionary à grande échelle.

## Architecture des providers

Tous les providers de synonymes implémentent le protocole `SynonymProvider` :

```python
from whoosh_modern.linguistics.synonyms import SynonymProvider

class MyProvider(SynonymProvider):
    def get_synonyms(self, word: str) -> list[str]: ...
    def add_synonym(self, word: str, synonyms: list[str]) -> None: ...
    def remove_synonym(self, word: str, synonym: str) -> None: ...
```

## Providers intégrés

### StaticSynonymProvider

Provider en mémoire sauvegardé par un dictionnaire :

```python
from whoosh_modern.linguistics.synonyms import StaticSynonymProvider

provider = StaticSynonymProvider({
    "voiture": ["automobile", "véhicule"],
    "maison": ["domicile", "résidence"],
})
print(provider.get_synonyms("voiture"))  # ['automobile', 'véhicule']
```

### YAMLSynonymProvider

Charge les synonymes depuis un fichier YAML :

```yaml
# synonyms.yaml
voiture:
  - automobile
  - véhicule
maison:
  - domicile
  - résidence
```

```python
from whoosh_modern.linguistics.synonyms import YAMLSynonymProvider

provider = YAMLSynonymProvider("synonyms.yaml")
print(provider.get_synonyms("voiture"))  # ['automobile', 'véhicule']
```

### JSONSynonymProvider

Charge les synonymes depuis un fichier JSON :

```json
{
    "voiture": ["automobile", "véhicule"],
    "maison": ["domicile", "résidence"]
}
```

```python
from whoosh_modern.linguistics.synonyms import JSONSynonymProvider

provider = JSONSynonymProvider("synonyms.json")
print(provider.get_synonyms("voiture"))
```

### WiktionarySynonymProvider

Charge les synonymes depuis un fichier JSON Lines kaikki.org :

```python
from whoosh_modern.linguistics.synonyms import WiktionarySynonymProvider

provider = WiktionarySynonymProvider(
    "src/whoosh_modern/linguistics/dictionaries/wiktionary/fr.json"
)
print(provider.get_synonyms("voiture"))  # ['automobile', 'véhicule']
```

Chaque ligne du fichier dictionnaire est un objet JSON :

```json
{"word": "voiture", "s": ["automobile", "véhicule"]}
{"word": "ordinateur", "s": ["pc", "machine"]}
```

Le provider filtre :
- Les mots contenant des espaces (expressions multi-mots)
- Les entrées avec parties du discours non standard
- Les listes de synonymes vides ou manquantes

### SQLiteSynonymStore

Store de synonymes persistant sauvegardé par SQLite :

```python
from whoosh_modern.linguistics.synonyms import SQLiteSynonymStore

store = SQLiteSynonymStore("synonyms.db")
store.add_synonym("voiture", ["automobile", "véhicule"])
print(store.get_synonyms("voiture"))  # ['automobile', 'véhicule']
store.close()
```

## SynonymManager

`SynonymManager` est l'interface de haut niveau pour gérer les synonymes :

```python
from whoosh_modern.linguistics.synonyms import SynonymManager

manager = SynonymManager({"voiture": ["automobile", "véhicule"]})

# CRUD
manager.add_synonyms("maison", ["domicile", "résidence"])
print(manager.get_synonyms("maison"))  # ['domicile', 'résidence']
manager.remove_synonym("maison", "domicile")

# Import depuis des sources externes
manager.import_yaml("synonyms.yaml")       # Requiert PyYAML
manager.import_json("synonyms.json")
manager.import_wiktionary("dictionaries/wiktionary/fr.json")

# Export
manager.export_json("output.json")
```

## Mise à jour des dictionnaires Wiktionary

Les dictionnaires pré-générés se trouvent dans `src/whoosh_modern/linguistics/dictionaries/wiktionary/` :

```
wiktionary/
├── fr.json
├── en.json
├── de.json
├── es.json
├── it.json
├── manifest.json
└── README.md
```

Pour les régénérer depuis le dernier dump kaikki.org :

```bash
python scripts/update_wiktionary_dictionaries.py --all
```

Ou pour une seule langue :

```bash
python scripts/update_wiktionary_dictionaries.py --lang fr
```

Le script télécharge `kaikki.org-dictionary-all.jsonl`, extrait les synonymes par langue, filtre par tags POS autorisés, et écrit des fichiers JSON Lines compacts par langue.

## SynonymExpansionMiddleware

Intègre l'expansion de synonymes dans le pipeline de middleware :

```python
from whoosh_modern.linguistics.synonyms import (
    SynonymManager,
    SynonymExpansionMiddleware,
)

manager = SynonymManager({
    "voiture": ["automobile", "véhicule"],
    "maison": ["domicile", "résidence"],
})
middleware = SynonymExpansionMiddleware(manager)
```

Le middleware étend à la fois les requêtes de recherche et les documents indexés :

```python
# Expansion de requête
ctx = MiddlewareContext(operation="search")
ctx.query = "voiture"
ctx = middleware.before_search(ctx)
# ctx.query == "voiture automobile véhicule"

# Expansion de document
ctx = MiddlewareContext(operation="index")
ctx.document = {"title": "maison à vendre"}
ctx = middleware.before_index(ctx)
# ctx.document["title"] == "maison à vendre domicile résidence"
```

## Synonymes préconstruits par langue

`LANG_SYNONYMS` fournit des dictionnaires de démarrage pour cinq langues :

```python
from whoosh_modern.linguistics.synonyms import LANG_SYNONYMS

french_syns = LANG_SYNONYMS["fr"]
print(french_syns["voiture"])  # ['automobile', 'véhicule']

english_syns = LANG_SYNONYMS["en"]
print(english_syns["car"])  # ['automobile', 'vehicle']
```

| Langue   | Code | Entrée exemple                          |
|----------|------|----------------------------------------|
| Français | `fr` | `"voiture": ["automobile", "véhicule"]` |
| Anglais  | `en` | `"car": ["automobile", "vehicle"]`      |
| Allemand | `de` | `"auto": ["wagen", "fahrzeug"]`         |
| Espagnol | `es` | `"coche": ["automóvil", "vehículo"]`    |
| Italien  | `it` | `"auto": ["automobile", "veicolo"]`     |

## Exemple d'intégration

```python
from whoosh_modern.linguistics import (
    LANG_SYNONYMS,
    SynonymExpansionMiddleware,
    SynonymManager,
)
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.wrappers import MiddlewareWriter, MiddlewareSearcher

# 1. Construit le manager de synonymes
syn_manager = SynonymManager(LANG_SYNONYMS["fr"])
syn_manager.add_synonyms("recherche", ["query", "cherche"])

# 2. Crée le middleware
syn_middleware = SynonymExpansionMiddleware(syn_manager)

# 3. Construit la chaîne de middleware
chain = MiddlewareChain([syn_middleware])

# 4. Utilise avec writer/searcher
with MiddlewareWriter(ix.writer(), chain) as writer:
    writer.add_document(title="Comment faire une recherche dans Whoosh")

with MiddlewareSearcher(ix.searcher(), chain) as searcher:
    results = searcher.search("recherche")
```

## Intégration de l'indexation Wiktionary

`WiktionaryIndexer` peut alimenter les synonymes directement dans `SynonymManager` et `SearchApplication`.

### SynonymManager.import_wiktionary_index()

Peuple un manager depuis un index Whoosh construit :

```python
from whoosh_modern.linguistics.synonyms import SynonymManager
from whoosh_modern.linguistics.wiktionary_indexer import WiktionaryIndexer

indexer = WiktionaryIndexer("indexdir")
# ... build_index() appelé précédemment ...

manager = SynonymManager()
manager.import_wiktionary_index("indexdir", language="fr")
print(manager.get_synonyms("voiture"))
# ['automobile', 'véhicule']
```

### Intégration SearchApplication

Passe un `WiktionaryIndexer` à `SearchApplication` pour exposer un `synonym_manager` pré-peuplé :

```python
from whoosh_modern import SearchApplication
from whoosh_modern.linguistics.wiktionary_indexer import WiktionaryIndexer

indexer = WiktionaryIndexer("indexdir")
app = SearchApplication(wiktionary_indexer=indexer)

# synonym_manager est peuplé paresseusement depuis l'index
manager = app.synonym_manager
```

### Câblage de SynonymExpansionMiddleware

Combine avec le middleware pour étendre les requêtes au moment de la recherche :

```python
from whoosh_modern.linguistics.synonyms import SynonymExpansionMiddleware

middleware = SynonymExpansionMiddleware(app.synonym_manager)
```

## Voir aussi

- [Vue d'ensemble linguistique](linguistics.md) — Stemmers, analyseurs de langue, et intégration complète du pipeline
- [Pipeline de middleware](middleware-pipeline.md) — Fonctionnement des chaînes de middleware
- [Providers de stemming](stemming-providers.md) — Backends de stemming spécifiques aux langues
