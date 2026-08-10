---
title: "Documentation Whoosh-NG"
nav_order: 1
lang: fr
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

> **Dernière version publiée**: v4.3.0 | [Voir les releases sur GitHub](https://github.com/dorel14/whoosh-ng/releases) | Dernière mise à jour: 2026-08-10

## Documentation

- **[API Reference]({{ '/fr/api/overview/' | relative_url }})** — Documentation complète des modules
- **[Guides]({{ '/fr/guides/' | relative_url }})** — Tutoriels et bonnes pratiques
- **[Exemples]({{ '/fr/examples/' | relative_url }})** — Exemples de code exécutables
- **[English Documentation]({{ '/en/' | relative_url }})** — Documentation in English

## Structure de la documentation

### Core (Whoosh classique)

- **[Démarrage rapide]({{ '/fr/quickstart/' | relative_url }})** — Tutoriel en 5 minutes
- **[Installation]({{ '/fr/guides/installation/' | relative_url }})** — Instructions d'installation
- **[Concepts fondamentaux]({{ '/fr/guides/core-concepts/' | relative_url }})** — Schémas, champs, recherche
- **[Indexation]({{ '/fr/guides/indexing/' | relative_url }})** — Ajout et mise à jour de documents
- **[Recherche]({{ '/fr/guides/searching/' | relative_url }})** — Analyse de requêtes et résultats
- **[Conception de schéma]({{ '/fr/guides/schema/' | relative_url }})** — Types de champs et stockage
- **[Langage de requête]({{ '/fr/guides/query/' | relative_url }})** — Syntaxe de requête style Lucene
- **[Backends]({{ '/fr/guides/backends/' | relative_url }})** — Stockage fichier, SQLite, mémoire
- **[Migration]({{ '/fr/guides/migration/' | relative_url }})** — Migration depuis Whoosh classique
- **[Nettoyage legacy]({{ '/fr/guides/legacy-cleanup/' | relative_url }})** — Suppression du code legacy

### Modern (Nouvelles fonctionnalités)

- **[Middleware]({{ '/fr/guides/middleware/' | relative_url }})** — Hooks de pipeline et middleware
- **[Middleware & Pipeline de Plugins]({{ '/fr/guides/middleware-sprint-c/' | relative_url }})** — Pipeline basé sur hooks
- **[Plugins]({{ '/fr/guides/plugins/' | relative_url }})** — Extension de Whoosh-NG
- **[Système de Plugins]({{ '/fr/guides/plugins-sprint-c/' | relative_url }})** — API PluginManager
- **[Autocomplétion]({{ '/fr/guides/autocomplete/' | relative_url }})** — Fournisseurs d'autocomplétion
- **[Fournisseurs d'Autocomplétion]({{ '/fr/guides/autocomplete-sprint-d/' | relative_url }})** — NGram, Fuzzy, InvertedIndex
- **[Recherche vectorielle]({{ '/fr/guides/vector/' | relative_url }})** — NumPy, HNSW, Faiss
- **[Indexation moderne]({{ '/fr/guides/modern-indexing/' | relative_url }})** — BatchIndexWriter, AnalyzerCache
- **[Monitoring]({{ '/fr/guides/monitoring/' | relative_url }})** — Métriques et observabilité
- **[Performance]({{ '/fr/guides/performance/' | relative_url }})** — Benchmarking et optimisation
- **[Synonymes & Linguistique]({{ '/fr/guides/linguistics-sprint-d/' | relative_url }})** — SynonymManager
- **[Fournisseurs de Stemmers]({{ '/fr/guides/stemming-sprint-d/' | relative_url }})** — Backends PyStemmer

### API Reference

- **[Modern API]({{ '/fr/api/modern/' | relative_url }})** — Sources de données, validation, facettes, middleware

### Exemples

- **[Indexation de base]({{ '/fr/examples/basic-indexing/' | relative_url }})** — Exemples d'indexation de documents
- **[Recherche]({{ '/fr/examples/search/' | relative_url }})** — Interrogation et récupération de résultats
- **[Modèles de recherche]({{ '/fr/examples/search-models/' | relative_url }})** — Auto-mapping des modèles Python vers Whoosh
- **[FastAPI]({{ '/fr/examples/fastapi-search/' | relative_url }})** — API REST avec FastAPI
- **[Middleware]({{ '/fr/examples/middleware/' | relative_url }})** — Patterns de middleware personnalisés
- **[Pipeline de middleware]({{ '/fr/examples/middleware-pipeline/' | relative_url }})** — Nouvelle tentative, cache, journalisation
- **[Application de recherche cinéma]({{ '/fr/examples/movie-search/' | relative_url }})** — Application de recherche complète
- **[Développement de plugins]({{ '/fr/examples/plugin-dev/' | relative_url }})** — Créer des plugins
- **[Sources de données]({{ '/fr/examples/data-sources/' | relative_url }})** — SQLSource, RESTSource, GraphQLSource, FastCSVSource, JSONSource, ParquetSource, PandasSource, PolarsSource, SQLAlchemySource, PeeweeSource, TortoiseSource
- **[Découverte de schéma]({{ '/fr/examples/schema-discovery/' | relative_url }})** — Inspection des jeux de résultats
- **[Gestionnaire de facettes]({{ '/fr/examples/facets/' | relative_url }})** — Auto-découverte et remplacements manuels
- **[Framework de validation]({{ '/fr/examples/validation/' | relative_url }})** — Validation 4 niveaux
- **[SearchView]({{ '/fr/examples/search-view/' | relative_url }})** — Intégration du pipeline complet
- **[Autocomplétion]({{ '/fr/examples/autocomplete/' | relative_url }})** — Exemples de fournisseurs d'autocomplétion
- **[Recherche vectorielle]({{ '/fr/examples/vector-search/' | relative_url }})** — Intégration NumPy, HNSW et Faiss

## Liens rapides

- **Dépôt GitHub**: [whoosh-ng](https://github.com/dorel14/whoosh-ng)
- **Paquet PyPI**: [whoosh-ng](https://pypi.org/project/whoosh-ng/)
- **Signalements de bugs**: [GitHub Issues](https://github.com/dorel14/whoosh-ng/issues)
- **Documentation pour LLM**:
  - [`llms.txt`]({{ '/llms.txt' | relative_url }}) — Index de toutes les pages de documentation
  - [`llms-full.txt`]({{ '/llms-full.txt' | relative_url }}) — Documentation API complète
