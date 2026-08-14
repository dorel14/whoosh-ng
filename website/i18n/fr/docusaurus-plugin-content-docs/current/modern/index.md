---
title: "Modern"
sidebar_position: 20
sidebars: docs
---

# Modern

Whoosh-NG est plus qu'un fork — c'est **l'évolution** de Whoosh pour les
applications Python modernes. Cette section documente les extensions optionnelles
et activables qui rendent Whoosh-NG prêt pour la production dans les stacks
d'aujourd'hui : recherche sémantique vectorielle, architecture à plugins,
pipeline de middleware, linguistique et stockage cloud enfichable.

> Toutes les fonctionnalités ici sont des **extras optionnels** : le moteur
> core ne possède aucune dépendance tierce obligatoire. Les fonctionnalités
> classiques résident sous [Core](/core).

## Points forts

```text
┌─────────────────────────────────────────────────────────────┐
│  Extensions Modern de Whoosh-NG                             │
├─────────────────────────────────────────────────────────────┤
│  🔌 Plugins        → PluginManager, découverte par entry-point│
│  🧩 Middleware     → hooks transverses indexation/recherche  │
│  🧠 Recherche Vec. → providers NumPy, HNSW, Faiss, Qdrant    │
│  🌐 Linguistique   → synonymes, analyseurs multi-langues     │
│  🔤 Stemming       → système de providers avec PyStemmer     │
│  ☁️  Stockage       → backends S3, hybrides cache + distant   │
│  ⚡ Performance    → guides de benchmark et d'optimisation   │
└─────────────────────────────────────────────────────────────┘
```

## Guides

| Guide | Description |
|-------|-------------|
| [Plugins](/modern/plugins) | L'architecture à plugins et l'enregistrement d'extensions |
| [Système de Plugins](/modern/plugins-avances) | API `PluginManager` et cycle de vie |
| [Middleware](/modern/middleware) | Classes de base et contexte middleware |
| [Middleware & Pipeline de Plugins](/modern/middleware-pipeline) | Composez des préoccupations transverses |
| [Autocomplétion](/modern/autocomplete) | Fournisseurs d'autocomplétion |
| [Fournisseurs d'Autocomplétion](/modern/autocomplete-fournisseurs) | Backends NGram, Fuzzy, InvertedIndex |
| [Recherche Vectorielle](/modern/vector) | Recherche sémantique par embeddings |
| [Indexation Moderne](/modern/modern-indexing) | `BatchIndexWriter`, `AnalyzerCache` |
| [Monitoring](/modern/monitoring) | Métriques et observabilité |
| [Performance](/modern/performance) | Benchmarking et optimisation |
| [Synonymes & Linguistique](/modern/linguistique) | `SynonymManager` et moteur linguistique |
| [Fournisseurs de Stemmers](/modern/stemmers-fournisseurs) | Backends PyStemmer et auto-détection |
| [Providers de Stockage](/modern/storage-providers) | Backends hybrides, S3 et asynchrones |
| [Embeddings](/modern/embeddings) | Provider d'embeddings ONNX Runtime compatible CPU |
| [Auto-indexation](/modern/auto-indexing) | Découverte de schéma et indexation pilotée par une source de données |
| [SearchApplication](/modern/search-application) | Point d'entrée unifié pour l'indexation et la recherche |
| [Intégration des Providers](/modern/provider-integration) | Intégration de bout en bout du pipeline |
| [Moteur de Configuration](/modern/configuration-engine) | Surface de configuration typée |

## Par où commencer

1. Nouveau sur Whoosh-NG ? Commencez par [Core → Démarrage rapide](/core/quickstart).
2. Vous voulez la recherche sémantique ? Consultez [Recherche Vectorielle](/modern/vector).
3. Vous construisez un service web ? Voir [Plugins](/modern/plugins) et
   [Providers de Stockage](/modern/storage-providers).

> 💡 Astuce : les guides classiques [Stemming](/core/stemming) et
> [N-grammes](/core/ngrams) se trouvent désormais sous **Core**, car ils font
> partie du jeu de fonctionnalités d'origine de Whoosh.
