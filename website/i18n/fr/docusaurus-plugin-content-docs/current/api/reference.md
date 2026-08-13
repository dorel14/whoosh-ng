---
title: "Référence API"
sidebar_position: 60
sidebars: apiSidebar
---

# Référence API

The Whoosh-NG API reference is générée automatiquement à partir du code source avec
[pydoctor](https://pydoctor.readthedocs.io/), qui analyse les modules Python
et génère une documentation HTML à partir des docstrings.

:::note
Si la documentation intégrée ne s'affiche pas, il se peut que les docs API
n'aient pas encore été générées dans ce déploiement. Consultez
[la page GitHub](https://github.com/dorel14/whoosh-ng/tree/master/website/static/api_docs)
pour la documentation API complète, ou reportez-vous à la
[liste des modules API](#api-modules) ci-dessous.
:::

## Modules API

### API Core

| Module | Description |
|--------|-------------|
| `whoosh.index` | Création, ouverture et gestion d'index de haut niveau |
| `whoosh.fields` | Schéma et définitions de types de champs |
| `whoosh.writing` | Classes d'écriture et politiques de fusion |
| `whoosh.searching` | Searcher, Results et collectors |
| `whoosh.query` | Classes de requêtes et parseurs |
| `whoosh.qparser` | Implémentation du parseur de requêtes |
| `whoosh.analysis` | Tokenizers, filtres et analyseurs |
| `whoosh.highlight` | Surlignage des résultats de recherche |
| `whoosh.spelling` | Correction orthographique |
| `whoosh.sorting` | Facettes et tri |
| `whoosh.event_bus` | Système d'événements |
| `whoosh.hooks` | Système de hooks |
| `whoosh.middleware` | Pipeline de middleware |
| `whoosh.plugins` | Système de plugins et registre |
| `whoosh.backends` | Backends de stockage |

### API Modern

| Module | Description |
|--------|-------------|
| `whoosh_modern.data_sources` | Protocole et implémentations de sources de données |
| `whoosh_modern.views` | Interface unifiée SearchView |
| `whoosh_modern.middleware` | Middleware de retry, cache, logging |
| `whoosh_modern.facets` | FacetManager pour l'auto-découverte |
| `whoosh_modern.validation` | Framework de validation à 4 niveaux |
| `whoosh_modern.indexing` | BatchIndexWriter, AnalyzerCache |
| `whoosh_modern.linguistics` | Moteur linguistique (stemmers, synonymes) |
| `whoosh_modern.storage` | Providers de stockage (HybridStorage, etc.) |
| `whoosh_modern.vector` | NumpyProvider pour la similarité vectorielle |
| `whoosh_modern.autocomplete` | Plugins de providers d'autocomplétion |
| `whoosh_fastapi` | Endpoints API REST FastAPI |
| `whoosh_admin` | Tableau de bord d'administration |

:::info
For the full interactive API documentation, run:
```bash
pip install pydoctor
python scripts/generate_api_docs.py
```
Then open `website/static/api_docs/index.html` in your browser.
:::
