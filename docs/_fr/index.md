---
title: "Documentation Whoosh-NG"
nav_order: 1
lang: fr
---

# Documentation Whoosh-NG

Bibliothèque d'indexation et de recherche full-text purement Python, modernisée pour 2025+.

## Démarrage rapide

```bash
pip install whoosh-ng
```

```python
import whoosh.index as index
from whoosh.fields import Schema, TEXT, ID

schema = Schema(id=ID(stored=True), content=TEXT())
ix = index.create_in("indexdir", schema)

with ix.writer() as w:
    w.add_document(id="1", content="hello world")

with ix.searcher() as s:
    results = s.search("world")
    print(results[0])
```

## Documentation

- **[API Reference]({{ '/fr/api/overview/' | relative_url }}))** — Documentation complète des modules
- **[Guides]({{ '/fr/guides/' | relative_url })}** — Tutoriels et bonnes pratiques
- **[Exemples]({{ '/fr/examples/' | relative_url })}** — Exemples de code exécutables
- **[English Documentation]({{ '/en/' | relative_url })}** — Documentation in English

## Structure de la documentation

### Guides utilisateur

- **[Indexation]({{ '/fr/guides/indexing/' | relative_url }})** — Ajouter, mettre à jour et supprimer des documents
- **[Recherche]({{ '/fr/guides/searching/' | relative_url }})** — Analyse de requêtes, surbrillance et facettes
- **[Conception de schéma]({{ '/fr/guides/schema/' | relative_url }})** — Types de champs, stockage et options d'indexation
    - **[Middleware]({{ '/fr/guides/middleware/' | relative_url }})** — Hooks de pipeline et middleware personnalisé
    - **[Middleware & Pipeline de Plugins]({{ '/fr/guides/middleware-sprint-c/' | relative_url }})** — Hooks de middleware et intégration PluginManager
    - **[Plugins]({{ '/fr/guides/plugins/' | relative_url }})** — Étendre Whoosh-NG avec des plugins
    - **[Système de Plugins]({{ '/fr/guides/plugins-sprint-c/' | relative_url }})** — API PluginManager, entry points et déploiement
    - **[Autocomplétion]({{ '/fr/guides/autocomplete/' | relative_url }})** — Fournisseurs d'autocomplétion
    - **[Fournisseurs d'Autocomplétion]({{ '/fr/guides/autocomplete-sprint-d/' | relative_url }})** — NGramProvider, FuzzySuggestProvider, InvertedIndexAutocomplete
    - **[Recherche vectorielle]({{ '/fr/guides/vector/' | relative_url }})** — Intégration NumPy, HNSW et Faiss
    - **[Performance]({{ '/fr/guides/performance/' | relative_url }})** — Outils de benchmarking et résultats d'optimisation
    - **[Indexation moderne]({{ '/fr/guides/modern-indexing/' | relative_url }})** — BatchIndexWriter, AnalyzerCache, FieldAnalyzerCache
    - **[Synonymes & Linguistique]({{ '/fr/guides/linguistics-sprint-d/' | relative_url }})** — SynonymManager, fournisseurs, middleware
    - **[Fournisseurs de Stemmers]({{ '/fr/guides/stemming-sprint-d/' | relative_url }})** — Backends de stemmers, PyStemmer, analyseurs linguistiques

### API Reference

- **[Modern API]({{ '/fr/api/modern/' | relative_url }})** — Sources de données, validation, facettes, middleware

### Exemples

- **[Indexation basique]({{ '/fr/examples/basic-indexing/' | relative_url }})** — Exemples d'indexation de documents
- **[Recherche]({{ '/fr/examples/search/' | relative_url }})** — Interrogation et récupération de résultats
- **[FastAPI]({{ '/fr/examples/fastapi/' | relative_url }})** — API REST avec FastAPI
- **[Middleware]({{ '/fr/examples/middleware/' | relative_url }})** — Patterns de middleware personnalisés
- **[Sources de données]({{ '/fr/examples/data-sources/' | relative_url }})** — SQLSource, RESTSource, GraphQLSource, FastCSVSource, JSONSource, ParquetSource, PandasSource, PolarsSource, SQLAlchemySource, PeeweeSource, TortoiseSource
- **[Découverte de schéma]({{ '/fr/examples/schema-discovery/' | relative_url }})** — Inspection des jeux de résultats
- **[Gestionnaire de facettes]({{ '/fr/examples/facets/' | relative_url }})** — Auto-découverte et remplacements manuels
- **[Framework de validation]({{ '/fr/examples/validation/' | relative_url }})** — Validation 4 niveaux
- **[SearchView]({{ '/fr/examples/search-view/' | relative_url }})** — Intégration du pipeline complet
- **[Pipeline de middleware]({{ '/fr/examples/middleware-pipeline/' | relative_url }})** — Nouvelle tentative, cache, journalisation
