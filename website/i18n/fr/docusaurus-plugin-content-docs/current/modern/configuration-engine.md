---
title: "Moteur de Configuration"
sidebar_position: 215
---

# Moteur de Configuration

Whoosh-NG intègre un **Moteur de Configuration** (`ConfigEngine`) qui charge,
valide et fusionne la configuration applicative depuis des fichiers YAML ou
JSON. Il repose sur des modèles Pydantic et prend en charge une organisation
hiérarchique par couches, permettant à des surcharges spécifiques à
l'environnement d'étendre proprement les réglages de base.

## Concepts de base

### Modèles Pydantic

Toute la configuration est exprimée via des modèles Pydantic typés :

- `WhooshNGConfig` — configuration applicative de plus haut niveau
- `FieldConfig` — options d'indexation par champ
- `SearchConfig` / `FuzzyConfig` / `RankingConfig` / `AIConfig`
- `DataSourceConfigModel` — connexion et synchronisation de la source de données
- `StorageConfigModel` — sélection du backend de stockage

### Chargeurs (loaders)

Deux chargeurs sont fournis :

- `load_yaml(path)` — analyse un fichier YAML en `dict`
- `load_json(path)` — analyse un fichier JSON en `dict`
- `load_config(path)` — détecte automatiquement le format depuis l'extension et
  renvoie un `WhooshNGConfig` validé

### Fusion hiérarchique

`ConfigEngine.load(path, priority=...)` et `ConfigEngine.merge(overrides, priority=...)`
empilent les sources de configuration selon l'ordre de priorité suivant (le plus
haut l'emporte) :

1. `runtime`
2. `instance`
3. `application`
4. `language`

Une valeur de ``priority`` invalide lève immédiatement ``ValueError``, afin
qu'une couche mal configurée ne puisse pas affecter silencieusement l'ordre de
fusion.

La fusion est profonde : les dictionnaires imbriqués sont fusionnés
récursivement. Les valeurs scalaires et les listes sont **remplacées
entièrement** par les valeurs de surcharge ; les listes ne sont PAS ajoutées ni
combinées. Par exemple, une configuration de base ``{"plugins": ["a", "b"]}``
surchargée par ``{"plugins": ["c"]}`` produit ``{"plugins": ["c"]}``, et non
``{"plugins": ["a", "b", "c"]}``. Si une fusion additive de listes est requise,
traitez-la au niveau applicatif avant d'appeler :meth:`ConfigEngine.merge`.

> [!WARNING]
> **Comportement de remplacement des listes** : lors de la fusion de
> configurations, les listes sont **completement écrasées** par les couches de
> priorité supérieure. Elles ne sont ni ajoutées, ni concaténées, ni
> dédupliquées. Il s'agit d'un choix de conception volontaire qui garantit un
> contrôle explicite du contenu des listes entre les couches et évite des états
> fusionnés imprévisibles. Si vous avez besoin d'un comportement additif (par
> exemple étendre une liste de plugins ou de middlewares), effectuez la logique
> de fusion dans votre code applicatif avant de passer le dictionnaire final à
> :meth:`ConfigEngine.merge`.

## Démarrage rapide

```python
from whoosh_modern.config import ConfigEngine

engine = ConfigEngine()
engine.load("whoosh-ng.yml", priority="application")
engine.load("whoosh-ng.local.yml", priority="instance")
engine.merge({"search": {"fuzzy": {"distance": 5}}}, priority="runtime")

config = engine.get_config()
print(config.index)
print(config.fields["title"].stemming)
print(config.search.fuzzy.distance)
```

## Exemple YAML

```yaml
# whoosh-ng.yml
index: products
languages:
  default: fr
fields:
  title:
    type: text
    language: fr
    stemming: true
    stored: true
  price:
    type: numeric
    sortable: true
search:
  fuzzy:
    enabled: true
    distance: 2
storage:
  type: file
  path: ./index
```

## Exemple JSON

```json
{
  "index": "products",
  "languages": {"default": "en"},
  "fields": {
    "title": {"type": "text", "language": "en", "stemming": true},
    "price": {"type": "numeric", "sortable": true}
  },
  "search": {"fuzzy": {"enabled": true, "distance": 2}},
  "storage": {"type": "file", "path": "./index"}
}
```

## Exemples YAML complets

### Configuration minimale

```yaml
# whoosh-ng.yml
index: my_index
fields:
  title:
    type: text
    stored: true
storage:
  type: file
  path: ./index
```

### Catalogue e-commerce avec source CSV

```yaml
# whoosh-ng.yml
index: products
fields:
  sku:
    type: text
    stored: true
    unique: true
  name:
    type: text
    language: fr
    stemming: true
    stored: true
  description:
    type: text
    language: fr
    stemming: true
  price:
    type: numeric
    sortable: true
    faceted: true
  category:
    type: text
    faceted: true
  published_at:
    type: datetime
    faceted: true
search:
  fuzzy:
    enabled: true
    distance: 2
data_source:
  type: csv
  path: Datas/products.csv
  delimiter: ","
  encoding: utf-8
  id_field: sku
storage:
  type: file
  path: ./index
```

### Configuration par couches (base + instance + runtime)

```yaml
# whoosh-ng.yml  (couche application)
index: app
fields:
  title:
    type: text
    stemming: true
search:
  fuzzy:
    enabled: true
    distance: 2
storage:
  type: file
  path: ./index
```

```yaml
# whoosh-ng.local.yml  (couche instance)
index: app-staging
storage:
  type: file
  path: ./index-staging
```

```python
# surcharge runtime dans le code
engine = ConfigEngine()
engine.load("whoosh-ng.yml", priority="application")
engine.load("whoosh-ng.local.yml", priority="instance")
engine.merge({"search": {"fuzzy": {"distance": 3}}}, priority="runtime")
app = engine.build()
```

## Exemples JSON complets

### Configuration minimale

```json
{
  "index": "my_index",
  "fields": {
    "title": {"type": "text", "stored": true}
  },
  "storage": {"type": "file", "path": "./index"}
}
```

### Configuration full-stack avec source SQL et stockage hybride

```json
{
  "index": "customers",
  "fields": {
    "customer_id": {"type": "numeric", "stored": true, "sortable": true},
    "first_name": {"type": "text", "language": "en", "stemming": true, "stored": true},
    "last_name": {"type": "text", "language": "en", "stemming": true, "stored": true},
    "city": {"type": "text", "language": "en", "stemming": true, "stored": true},
    "country": {"type": "text", "stored": true},
    "signup_date": {"type": "datetime", "faceted": true}
  },
  "search": {
    "fuzzy": {"enabled": true, "distance": 2},
    "highlight": {"enabled": true, "fragment_size": 200}
  },
  "data_source": {
    "type": "sql",
    "connection_string": "sqlite:///benchmark_data.db",
    "query": "SELECT * FROM customers",
    "id_field": "customer_id"
  },
  "storage": {
    "type": "hybrid",
    "local_path": "./index-cache",
    "remote": {
      "type": "s3",
      "bucket": "my-bucket",
      "prefix": "whoosh-indexes/"
    }
  }
}
```

## Configuration sans code avec ConfigEngine.build()

```python
from whoosh_modern.config import ConfigEngine

engine = ConfigEngine()
engine.load("whoosh-ng.yml")
app = engine.build()
app.build()

# Ajouter des documents via l'index writer
writer = app.index.writer()
writer.add_document(title="Premier cours de Python", body="...")
writer.add_document(title="Whoosh-NG avancé", body="...")
writer.commit()

# Ou utiliser la source directement pour un indexage en flux/lot
for doc in app._source.iter_documents():
    with app.index.writer() as writer:
        writer.add_document(**doc)

results = app.search("python")
```

## Référence des modules

| Module | Rôle |
|---|---|
| `whoosh_modern.config.models` | Modèles Pydantic de validation |
| `whoosh_modern.config.loader` | Chargeurs de fichiers YAML / JSON |
| `whoosh_modern.config.engine` | `ConfigEngine` avec fusion hiérarchique |

## Voir aussi

- [Providers de Stockage](storage-providers.md) — Backends configurables via `StorageConfigModel`
- [Sources de Données](data-sources.md) — `DataSourceConfigModel` et configuration des providers
