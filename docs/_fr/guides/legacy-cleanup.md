---
title: "Stratégie de nettoyage du code legacy"
nav_order: 60
lang: fr
---

# Stratégie de nettoyage du code legacy

Ce guide explique comment Whoosh-NG sépare le code moderne typé du code legacy,
et comment le nettoyage progressif est organisé.

## Pourquoi une frontière legacy ?

`whoosh-modern` est la nouvelle surface de Whoosh-NG, entièrement typée.
Le package `whoosh` original fonctionne toujours au runtime, mais il contient
des décennies de motifs de compatibilité Python 2/3, de métaprogrammation
dynamique et d'internes non typés. Forcer des types stricts sur l'ensemble
d'un coup bloquerait le développement.

La stratégie de nettoyage est **incrémentale et opt-in** :

1. `src/whoosh_modern/` est typé et vérifié avec `pyright` et `mypy` en mode strict.
2. `src/whoosh/` est la surface legacy. Elle est divisée en :
   - **modules exclus** (documentés dans `pyrightconfig.json`) — code trop
     dynamique ou vendu pour justifier un passage de types rentable maintenant ;
   - **candidats au nettoyage** — petits fichiers isolés, faciles à annoter et
     à vérifier.
3. Chaque sprint, une vague de candidats est typée, testée, puis sortie de la
   zone de tolérance élevée.

## Seuils actuels (Sprint 2)

| Vérificateur | Portée | Seuil |
|--------------|--------|-------|
| `pyright` | `src/whoosh_modern/` | **0 erreur** (strict) |
| `pyright` | legacy | **≤ 500 erreurs** (tolérant) |
| `mypy` | `src/` | **0 erreur** (via overrides + `ignore_errors`) |

## Justification des exclusions (`pyrightconfig.json`)

La liste `exclude` de `pyrightconfig.json` regroupe les fichiers par thème :

- **Vendu / sans stubs** : `pyparsing.py`, `relativedelta.py`
- **Shims de migration** : `codec/whoosh2.py`, `codec/whoosh3.py`
- **Parsing dynamique** : `qparser/`, `query/`, `analysis/`, `automata/`
- **Stockage fichiers** : `filedb/`, `reading/`, `writing/`
- **Heuristique / data-driven** : `lang/dmetaphone.py`, `lang/lovins.py`,
  `lang/phonetic.py`, `lang/wordnet.py`
- **Objets dynamiques** : `classify.py`, `index.py`, `locking.py`,
  `formats.py`, `middleware/`
- **Bas niveau vendu** : `support/bench.py`, `support/base85.py`,
  `support/bitstream.py`, `support/bitvector.py`, `support/charset.py`,
  `support/levenshtein.py`

## Plan Sprint 2

Pour le Sprint 2, l'accent est mis sur les petits modules utilitaires et de
support, sans dépendances externes ni métaprogrammation lourde.

Vague de candidats :

- `src/whoosh/util/varints.py`
- `src/whoosh/util/text.py`
- `src/whoosh/util/loading.py`
- `src/whoosh/support/bitstream.py`
- `src/whoosh/support/levenshtein.py`

Pour chaque fichier :

1. Supprimer le `# type: ignore` global (si présent).
2. Ajouter des signatures de fonctions précises.
3. Lancer `pyright` et `mypy` pour confirmer **0 nouvelle erreur**.
4. Retirer le fichier des exclusions de `pyrightconfig.json`.
5. Ajouter un test de régression dans `tests/test_legacy_cleanup.py`.

## Objectif long terme

Chaque fichier de `src/whoosh/` doit finir par être vérifiable par `mypy` et
`pyright` sans exclusion globale. D'ici là, la liste d'exclusion est le
registre explicite de la dette, et chaque sprint la réduit.
