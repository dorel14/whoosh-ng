---
title: "Référence API"
sidebar_position: 60
sidebars: apiSidebar
---

# Référence API

La référence API de Whoosh-NG est générée automatiquement à partir du code source avec
[pydoctor](https://pydoctor.readthedocs.io/), qui analyse les modules Python
et génère une documentation HTML à partir des docstrings.

:::note
Si la documentation intégrée ne s'affiche pas, les docs API peuvent ne pas
avoir été générées dans ce déploiement. [Voir sur GitHub](https://github.com/dorel14/whoosh-ng/tree/master/website/static/api_docs) pour la documentation complète, ou consultez la liste des modules ci-dessous.
:::

## Modules API

### API Core

| Module | Description |
|--------|-------------|
| `whoosh.index` | Création, ouverture et gestion d'index |
| `whoosh.fields` | Définitions de schémas et de types de champs |
| `whoosh.writing` | Classes Writer et politiques de fusion |
| `whoosh.searching` | Searcher, Results et collecteurs |
| `whoosh.query` | Classes et analyseurs de requêtes |
| `whoosh.qparser` | Analyseur de requêtes |
| `whoosh.analysis` | Tokenizers, filtres et analyseurs |
| `whoosh.highlight` | Surlignage des résultats de recherche |
| `whoosh.spelling` | Correction orthographique |
| `whoosh.sorting` | Facettes et tri |
| `whoosh.event_bus` | Système d'événements |
| `whoosh.hooks` | Système de hooks |
| `whoosh.middleware` | Pipeline de middleware |
| `whoosh.plugins` | Système et registre de plugins |
| `whoosh.backends` | Backends de stockage |

### API Moderne

| Module | Description |
|--------|-------------|
| `whoosh_modern.data_sources` | Protocole et implémentations de sources de données |
| `whoosh_modern.views` | Interface unifiée SearchView |
| `whoosh_modern.middleware` | Middleware de retry, cache, logging |
| `whoosh_modern.facets` | FacetManager pour la découverte automatique |
| `whoosh_modern.validation` | Framework de validation à 4 niveaux |
| `whoosh_modern.indexing` | BatchIndexWriter, AnalyzerCache |
| `whoosh_modern.linguistics` | Moteur linguistique (stemmers, synonymes) |
| `whoosh_modern.storage` | Fournisseurs de stockage (HybridStorage, etc.) |
| `whoosh_modern.vector` | NumpyProvider pour la similarité vectorielle |
| `whoosh_modern.autocomplete` | Plugins de fournisseurs d'autocomplétion |
| `whoosh_fastapi` | Points de terminaison REST API FastAPI |
| `whoosh_admin` | Interface d'administration |

:::info
Pour la documentation API interactive complète, exécutez :
```bash
pip install pydoctor
python scripts/generate_api_docs.py
```
Puis ouvrez `website/static/api_docs/index.html` dans votre navigateur.
:::
