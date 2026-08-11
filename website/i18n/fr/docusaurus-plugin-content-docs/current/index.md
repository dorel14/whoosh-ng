---
title: "Documentation Whoosh-NG"
sidebar_position: 1
sidebars: docs
---

# Documentation Whoosh-NG

Bibliothèque d'indexation et de recherche full-text purement Python, modernisée pour 2025+.

## Vitesse de démarrage

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

> **Derniere version publiee**: v4.3.0 | [Voir les releases sur GitHub](https://github.com/dorel14/whoosh-ng/releases) | Derniere mise a jour: 2026-08-11

## Documentation

- **[API Reference](/api/overview)** — Documentation complète des modules
- **[Guides](/core)** — Tutoriels et bonnes pratiques
- **[Exemples](/examples/basic-indexing)** — Exemples de code exécutables
- **[English Documentation](https://dorel14.github.io/whoosh-ng/)** — Documentation in English

## Structure de la documentation

### Core (Whoosh classique)

- **[Démarrage rapide](/core/quickstart)** — Tutoriel en 5 minutes
- **[Installation](/core/installation)** — Instructions d'installation
- **[Concepts fondamentaux](/core/core-concepts)** — Schémas, champs, recherche
- **[Indexation](/core/indexing)** — Ajout et mise à jour de documents
- **[Recherche](/core/searching)** — Analyse de requêtes et résultats
- **[Conception de schéma](/core/schema)** — Types de champs et stockage
- **[Langage de requête](/core/query)** — Syntaxe de requête style Lucene
- **[Backends](/core/backends)** — Stockage fichier, SQLite, mémoire
- **[Migration](/core/migration)** — Migration depuis Whoosh classique
- **[Nettoyage legacy](/core/legacy-cleanup)** — Suppression du code legacy

### Modern (Nouvelles fonctionnalités)

- **[Middleware](/modern/middleware)** — Hooks de pipeline et middleware
- **[Middleware & Pipeline de Plugins](/modern/middleware-pipeline)** — Pipeline basé sur hooks
- **[Plugins](/modern/plugins)** — Extension de Whoosh-NG
- **[Système de Plugins](/modern/plugins-avances)** — API PluginManager
- **[Autocomplétion](/modern/autocomplete)** — Fournisseurs d'autocomplétion
- **[Fournisseurs d'Autocomplétion](/modern/autocomplete-fournisseurs)** — NGram, Fuzzy, InvertedIndex
- **[Recherche vectorielle](/modern/vector)** — NumPy, HNSW, Faiss
- **[Indexation moderne](/modern/modern-indexing)** — BatchIndexWriter, AnalyzerCache
- **[Monitoring](/modern/monitoring)** — Métriques et observabilité
- **[Performance](/modern/performance)** — Benchmarking et optimisation
- **[Synonymes & Linguistique](/modern/linguistique)** — SynonymManager
- **[Fournisseurs de Stemmers](/modern/stemmers-fournisseurs)** — Backends PyStemmer
- **[Intégration des Providers](/modern/provider-integration)** — Guide complet du pipeline pour tous les providers

### API Reference

- **[Modern API](/api/modern)** — Sources de données, validation, facettes, middleware

### Exemples

- **[Indexation de base](/examples/basic-indexing)** — Exemples d'indexation de documents
- **[Recherche](/examples/search)** — Interrogation et récupération de résultats
- **[Modèles de recherche](/examples/search-models)** — Auto-mapping des modèles Python vers Whoosh
- **[FastAPI](/examples/fastapi-search)** — API REST avec FastAPI
- **[Middleware](/examples/middleware)** — Patterns de middleware personnalisés
- **[Pipeline de middleware](/examples/middleware-pipeline)** — Nouvelle tentative, cache, journalisation
- **[Application de recherche cinéma](/examples/movie-search)** — Application de recherche complète
- **[Développement de plugins](/examples/plugin-dev)** — Créer des plugins
- **[Sources de données](/examples/data-sources)** — SQLSource, RESTSource, GraphQLSource, FastCSVSource, JSONSource, ParquetSource, PandasSource, PolarsSource, SQLAlchemySource, PeeweeSource, TortoiseSource
- **[Découverte de schéma](/examples/schema-discovery)** — Inspection des jeux de résultats
- **[Gestionnaire de facettes](/examples/facets)** — Auto-découverte et remplacements manuels
- **[Framework de validation](/examples/validation)** — Validation 4 niveaux
- **[SearchView](/examples/search-view)** — Intégration du pipeline complet
- **[Autocomplétion](/examples/autocomplete)** — Exemples de fournisseurs d'autocomplétion
- **[Recherche vectorielle](/examples/vector-search)** — Intégration NumPy, HNSW et Faiss

## Liens rapides

- **Dépôt GitHub**: [whoosh-ng](https://github.com/dorel14/whoosh-ng)
- **Paquet PyPI**: [whoosh-ng](https://pypi.org/project/whoosh-ng/)
- **Signalements de bugs**: [GitHub Issues](https://github.com/dorel14/whoosh-ng/issues)
- **Documentation pour LLM**:
  - [`llms.txt`](/llms.txt) — Index de toutes les pages de documentation
  - [`llms-full.txt`](/llms-full.txt) — Documentation API complète
