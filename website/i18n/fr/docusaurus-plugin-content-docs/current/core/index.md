---
title: "Core"
sidebar_position: 1
sidebars: docs
---

# Core

Whoosh-NG s'appuie sur les fondations éprouvées de la bibliothèque **Whoosh**
d'origine. Cette section documente les **fonctionnalités classiques de recherche
full-text** qui propulsent Whoosh depuis plus d'une décennie — le moteur, le
schéma, les analyseurs, le scoring, et tous les concepts nécessaires pour
construire une recherche fiable.

> Ces fonctionnalités sont stables, compatibles avec Whoosh 1.x/2.x, et résident
> dans le package `whoosh`. Les nouvelles extensions optionnelles (recherche
> vectorielle, plugins, middleware, providers de stockage) sont documentées
> sous [Modern](/modern).

## Ce que vous trouverez ici

| Guide | Description |
|-------|-------------|
| [Démarrage rapide](/core/quickstart) | Indexez vos premiers documents en cinq minutes |
| [Installation](/core/installation) | Installez Whoosh-NG et ses extras optionnels |
| [Introduction à Whoosh](/core/intro) | Ce qu'est Whoosh et ce qu'il peut faire pour vous |
| [Concepts fondamentaux](/core/core-concepts) | Index, Schema, Writer, Searcher et flux de données |
| [À propos des analyseurs](/core/analysis) | Tokenizers, filtres et pipeline d'analyse |
| [Conception de schéma](/core/schema) | Types de champs et modélisation de vos documents |
| [Indexation](/core/indexing) | Ajout, mise à jour et suppression de documents |
| [Recherche](/core/searching) | Exécution de requêtes, résultats, tri et filtres |
| [Langage de requête](/core/query) | Syntaxe de requête Whoosh et `QueryParser` |
| [Stemming & Mots Vides](/core/stemming) | Réduction des mots à leur racine et filtrage du bruit |
| [N-grammes](/core/ngrams) | Correspondance de sous-chaînes, préfixes et autocomplétion |
| [Dates & Plages Numériques](/core/dates) | Requêtes et facettes sur nombres/dates |
| [Tri](/core/sorting) | Facettes et clés de tri pour ordonner les résultats |
| [Surlignage](/core/highlight) | Construire des extraits de résultats surlignés |
| [Voulez-vous dire...](/core/spelling) | Correction des fautes de frappe dans les requêtes |
| [Expansion de requête & Mots-clés](/core/keywords) | Extraction de mots-clés et « more like this » |
| [Documents Imbriqués](/core/nested) | Hiérarchies de documents parent-enfant |
| [Concurrence & Verrouillage](/core/threads) | Threads, verrous d'écriture et versionnage |
| [Indexation par Lot](/core/batch) | Astuces pour accélérer les gros indexages |
| [Caches de Champs](/core/fieldcaches) | Comportement de cache pour tri et facettes |
| [Recettes Whoosh](/core/recipes) | Extraits de code utiles pour les tâches courantes |

## Pipeline d'analyse classique

Whoosh transforme du texte brut en tokens recherchables via un pipeline
composable :

```
Texte  →  Tokenizer  →  Filtres (minuscules, mots vides, stemming)  →  Termes indexés
```

Les guides [Stemming & Mots Vides](/core/stemming) et
[N-grammes](/core/ngrams) montrent comment personnaliser ce pipeline selon
votre langue et votre cas d'usage.

## Référence

- [Glossaire](/core/glossary) — Termes clés utilisés dans toute la documentation
- [Guide de Migration](/core/migration) — Passage depuis Whoosh ou Whoosh-Reloaded
- [Stratégie de Nettoyage Legacy](/core/legacy-cleanup) — Évolution de la surface typée moderne

## Prochaines étapes

Prêt pour les nouveautés ? Rendez-vous dans [Modern](/modern) pour découvrir la
recherche vectorielle, le système de plugins, le pipeline de middleware et le
stockage enfichable.
