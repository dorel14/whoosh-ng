---
title: 'Glossaire'
sidebar_position: 100
---

# Glossaire

Un glossaire des termes clés utilisés dans Whoosh.

## Analyse

Le processus de conversion du texte en jetons (unités individuelles comme
les mots ou les termes) pour l'indexation. Implique la tokenisation, la
normalisation (mise en minuscules, racinement) et le filtrage (suppression
des mots vides, etc.).

## Analyseur

Une chaîne d'objets `Tokenizer` et `Filter` qui traite le texte en jetons.
Exemples : `RegexTokenizer`, `NgramTokenizer`, `LowercaseFilter`,
`StopFilter`, `StemmerFilter`.

## Fichier composé

Un format de fichier qui combine plusieurs fichiers de segment d'index
en un seul fichier `.seg`. Cela peut améliorer les performances sur
certains systèmes de fichiers en réduisant l'utilisation des descripteurs
de fichiers. Configuré via le paramètre `should_assemble` du codec.

## Document

Un enregistrement unique dans l'index, similaire à une ligne dans une base
de données. Un document contient des champs (analogues aux colonnes).

## Champ

Un attribut nommé d'un document. Les champs ont un type (défini par
`FieldType`) qui détermine comment la valeur du champ est indexée et
stockée.

## Type de champ

La classe (ex. : `TEXT`, `ID`, `NUMERIC`, `DATETIME`, `BOOLEAN`) qui
définit comment la valeur d'un champ est tokenisée, stockée, indexée, et
rendue triable/facetable.

## Filtre

Un composant d'`Analyzer` qui traite, transforme ou filtre les jetons
après la tokenisation. Exemples : `LowercaseFilter`, `StopFilter`,
`StemmerFilter`.

## Format

Un objet `Format` contrôle comment les informations de posting (fréquence
du terme, positions, décalages de caractères) sont encodées pour chaque
champ dans l'index inversé.
Exemples : `Existence`, `Frequency`, `Positions`, `Characters`.

## Fragmentation

Le processus de sélection des fragments de texte autour des termes
correspondants pour la mise en évidence.

## Mise en évidence (Highlighter)

Le module `whoosh.highlight`, qui fournit des formateurs, fragmenteurs
et évaluateurs pour mettre en évidence les termes de recherche dans les
documents.

## Index

La collection de fichiers de segment qui stockent l'index inversé, les
données de documents et les métadonnées (la table des matières, ou TOC).

## IndexWriter

La classe `IndexWriter` est utilisée pour créer et modifier l'index. Elle
met en mémoire tampon les ajouts et suppressions de documents et les
valide sur le disque.

## Index inversé (Inverted Index)

La structure de données centrale d'un moteur de recherche : pour chaque
terme unique, il stocke une liste de documents (et de positions) où ce
terme apparaît.

## Correspondance (Matcher)

Un objet qui itère sur les documents correspondants dans la liste de
postings pour une requête. Les correspondances peuvent être combinées
(union, intersection, etc.) pour des requêtes composées.

## Posting

Une entrée unique dans l'index inversé : un tuple
(ID de document, fréquence du terme, valeur) pour un terme donné.

## Schéma (Schema)

Définit les champs, leurs types et les options d'indexation. Un schéma
est passé à `Storage.create_index()`.

## Évaluateur (Scorer)

Un objet qui calcule un score de pertinence pour un document donné une
requête et des poids de termes. Les différents modèles de pondération
(BM25, TF-IDF, etc.) utilisent des évaluateurs différents.

## Segment

Une portion autonome de l'index inversé. Un index peut consiste en
plusieurs segments. Les segments sont fusionnés périodiquement (lors de
l'optimisation ou des opérations de fusion) pour améliorer les
performances.

## Clé de tri (Sort Key)

Une valeur calculée par document (via un `FacetType` et son
`Categorizer`) utilisée pour ordonner les résultats lors du tri et de la
facettisation.

## Racinement (Stemming)

Le processus de réduction des mots à leur forme racine (par ex.,
"running" → "run", "cats" → "cat") pour améliorer le rappel en
correspondant les formes inflectées.

## Mots vides (Stop Words)

Des mots à haute fréquence et faible information (ex. : "the", "a",
"and") qui sont généralement filtrés lors de l'indexation.

## Terme

Un couple unique (nom de champ, texte du jeton) dans l'index inversé.

## Vecteur de termes (Term Vector)

Structure de données optionnelle par document stockant les termes (et
optionnellement les positions et décalages de caractères) qui apparaissent
dans le champ d'un document, permettant des fonctionnalités comme la mise
en évidence et les retours de pertinence pseudo.

## Tokeniseur (Tokenizer)

Un composant d'`Analyzer` qui divise le texte d'entrée en jetons.
Exemples : `RegexTokenizer`, `PathTokenizer`, `NgramTokenizer`.

## Requête Whoosh

La syntaxe de requête propre à Whoosh, analysée par `QueryParser`.
Prend en charge la recherche sur champs, les requêtes de phrase, les
jokers, les intervalles et plus encore.
