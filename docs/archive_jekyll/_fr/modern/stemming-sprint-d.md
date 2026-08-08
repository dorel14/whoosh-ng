---
title: "Fournisseurs de Stemmers"
nav_order: 53
permalink: /fr/guides/stemming-sprint-d/
lang: fr
---

# Fournisseurs de Stemmers

Module: `whoosh_modern.analysis.stemmer_providers`, `whoosh_modern.analysis.stemming_analyzer`, `whoosh_modern.linguistics.stemmers`
Version: 2.0.0

Le système de fournisseurs de stemmers donne un contrôle flexible sur le backend de stemming utilisé pour l'analyse de texte. Il prend en charge la détection automatique, la sélection explicite du backend et l'enregistrement de stemmers personnalisés — le tout avec une API propre de type plugin.

## Vue d'ensemble du module

```text
whoosh_modern.analysis
    ├── stemmer_providers.py   # Protocole StemmerProvider, fournisseurs Internal/PyStemmer, register_stemmer, get_stemmer
    └── stemming_analyzer.py   # StemmingAnalyzer amélioré avec support plugin

whoosh_modern.linguistics.stemmers
    └── __init__.py            # Analyseurs linguistiques (FR/EN/DE/ES/IT)
```

## Protocole StemmerProvider

Situé dans `whoosh_modern.analysis.stemmer_providers` :

```python
from whoosh_modern.analysis.stemmer_providers import StemmerProvider

class MyStemmer(StemmerProvider):
    def stem(self, word: str) -> str:
        """Réduire un mot à sa racine."""
        ...

    @property
    def name(self) -> str:
        """Retourner le nom du stemmer."""
        return "my_stemmer"

    @property
    def language(self) -> str:
        """Retourner le code de langue."""
        return "english"
```

## Obtenir un Stemmer

### Détection Automatique (Recommandé)

La fonction `get_stemmer("auto", language)` sélectionne automatiquement le meilleur backend disponible :

```python
from whoosh_modern.analysis.stemmer_providers import get_stemmer

# Détection automatique : préfère PyStemmer si installé, sinon fallback interne
stemmer = get_stemmer("auto", "english")
print(stemmer.stem("running"))  # "run"
print(stemmer.name)             # "pystemmer" ou "internal"
```

**Ordre de priorité :**
1. **PyStemmer** (le plus rapide, nécessite `pip install whoosh-ng[fast-stemming]`)
2. **Stemmer interne** (Porter, toujours disponible)

### Sélection Explicite du Backend

```python
from whoosh_modern.analysis.stemmer_providers import get_stemmer

# Forcer le stemmer interne
stemmer = get_stemmer("internal", "english")

# Forcer PyStemmer (nécessite l'installation)
stemmer = get_stemmer("pystemmer", "english")
```

### Lister les Backends Disponibles

```python
from whoosh_modern.analysis.stemmer_providers import list_available_backends

backends = list_available_backends()
print(backends)
# {'internal': 'available', 'pystemmer': 'available', 'my_custom': 'registered'}
```

| Backend       | Chaîne de statut    | Nécessite                          |
|---------------|---------------------|-------------------------------------|
| `internal`    | `"available"`       | Aucun (toujours inclus)             |
| `pystemmer`   | `"available"` / `"not installed"` | `pip install whoosh-ng[fast-stemming]` |
| Personnalisé  | `"registered"`      | Enregistré via `@register_stemmer` |

## Fournisseurs de Stemmers Intégrés

### InternalStemmerProvider

Enveloppe le stemmer Porter intégré de Whoosh. Toujours disponible (aucune dépendance externe) :

```python
from whoosh_modern.analysis.stemmer_providers import InternalStemmerProvider

stemmer = InternalStemmerProvider("english")
print(stemmer.stem("cats"))    # "cat"
print(stemmer.stem("running")) # "run"
```

### PyStemmerProvider

Enveloppe la bibliothèque `Stemmer` pour un stemming haute performance. Supporte toutes les langues Snowball :

```python
from whoosh_modern.analysis.stemmer_providers import PyStemmerProvider

# Nécessite: pip install whoosh-ng[fast-stemming]
stemmer = PyStemmerProvider("english")
print(stemmer.stem("cats"))    # "cat"
```

**Note** : Ce fournisseur appelle `self._stemmer.stemWord(word)` pour réduire les mots. Assurez-vous que PyStemmer est installé ou la détection automatique basculera vers le stemmer interne.

### IdentityStemmerProvider

Un stemmer sans opération pour les tests ou lorsque le stemming n'est pas souhaité :

```python
from whoosh_modern.analysis.stemmer_providers import IdentityStemmerProvider

stemmer = IdentityStemmerProvider()
print(stemmer.stem("anything"))  # "anything"
```

## Enregistrer un Stemmer Personnalisé

Utilisez le décorateur `@register_stemmer` :

```python
from whoosh_modern.analysis.stemmer_providers import register_stemmer

@register_stemmer("simple")
class SimpleStemmer:
    def stem(self, word: str) -> str:
        # Suppression simple de suffixe
        if word.endswith("s") and len(word) > 3:
            return word[:-1]
        return word

    @property
    def name(self) -> str:
        return "simple"

    @property
    def language(self) -> str:
        return "english"

# Maintenant l'utiliser
from whoosh_modern.analysis.stemmer_providers import get_stemmer

stemmer = get_stemmer("simple", "english")
print(stemmer.stem("cats"))  # "cat"
```

## StemmingAnalyzer (Amélioré)

Situé dans `whoosh_modern.analysis.stemming_analyzer`, c'est le point d'entrée principal pour créer des analyseurs linguistiques :

```python
from whoosh_modern.analysis import StemmingAnalyzer

# Détection automatique du meilleur stemmer pour l'anglais
analyzer = StemmingAnalyzer(stemmer="auto", language="english")

# Stemmer interne explicite
analyzer = StemmingAnalyzer(stemmer="internal", language="english")

# Backend PyStemmer (si installé)
analyzer = StemmingAnalyzer(stemmer="pystemmer", language="french")

# Instance de fournisseur de stemmer personnalisé
analyzer = StemmingAnalyzer(stemmer=my_stemmer_instance)
```

### Paramètres de StemmingAnalyzer

| Paramètre   | Type                          | Défaut                   | Description                      |
|-------------|-------------------------------|--------------------------|----------------------------------|
| `expression`| Motif regex                   | motif de token par défaut | Tokenisation regex             |
| `stoplist`  | Itérable de mots vides        | `whoosh.analysis.STOP_WORDS` | Mots vides à filtrer         |
| `minsize`   | `int`                         | `2`                      | Longueur minimale du token       |
| `maxsize`   | `int \| None`                 | `None`                   | Longueur maximale du token       |
| `gaps`      | `bool`                        | `False`                  | Diviser sur l'expression vs correspondre |
| `stemmer`   | `str \| StemmerProvider`      | `"auto"`                 | Backend de stemmer               |
| `language`  | `str`                         | `"english"`              | Code de langue                   |
| `ignore`    | `set[str] \| None`            | `None`                   | Mots à ignorer                   |
| `cachesize` | `int`                         | `50000`                  | Taille du cache de stemming      |

### Utilisation avec les Types de Champs

```python
from whoosh_modern.analysis import StemmingAnalyzer
from whoosh.fields import Schema, TEXT

# Stemmer anglais avec mots vides
en_analyzer = StemmingAnalyzer("auto", language="english")

# Stemmer français
fr_analyzer = StemmingAnalyzer("auto", language="french")

schema = Schema(
    title=TEXT(stored=True),
    content_en=TEXT(analyzer=en_analyzer),
    content_fr=TEXT(analyzer=fr_analyzer),
)
```

## Analyseurs Linguistiques Spécifiques

Des analyseurs prêts à l'emploi pour cinq langues, disponibles dans `whoosh_modern.linguistics.stemmers` :

```python
from whoosh_modern.linguistics.stemmers import (
    EnglishAnalyzer,
    FrenchAnalyzer,
    GermanAnalyzer,
    SpanishAnalyzer,
    ItalianAnalyzer,
)

# Chaque analyseur est appelable et retourne une liste de tokens
en = EnglishAnalyzer()
tokens = en("The quick brown foxes")
# les tokens sont stemmés: ["quick", "brown", "fox"] (mots vides comme "the" supprimés)
```

### Analyseurs Linguistiques Disponibles

| Classe             | Langue    | Module                              |
|-------------------|-----------|-------------------------------------|
| `EnglishAnalyzer` | Anglais   | `whoosh_modern.linguistics.stemmers` |
| `FrenchAnalyzer`  | Français  | `whoosh_modern.linguistics.stemmers` |
| `GermanAnalyzer`  | Allemand  | `whoosh_modern.linguistics.stemmers` |
| `SpanishAnalyzer` | Espagnol  | `whoosh_modern.linguistics.stemmers` |
| `ItalianAnalyzer` | Italien   | `whoosh_modern.linguistics.stemmers` |

Chaque analyseur utilise en interne `get_stemmer("auto", language)` pour sélectionner le meilleur backend disponible et applique des mots vides spécifiques à la langue.

## Validation de la Compatibilité des Stemmers

Validez qu'un fournisseur de stemmer fonctionne correctement avec un ensemble de mots de test :

```python
from whoosh_modern.analysis.stemmer_providers import (
    get_stemmer,
    validate_stemmer_compatibility,
)

stemmer = get_stemmer("auto", "english")
report = validate_stemmer_compatibility(stemmer, ["running", "cats", "jumps", "houses"])

print(report["total_words"])   # 4
print(report["successful"])    # 4 (ou moins si erreurs)
print(report["failed"])        # 0
print(report["results"])       # [{'word': 'running', 'stemmed': 'run', 'success': True}, ...]
```

### Structure du Rapport de Compatibilité

| Champ          | Type       | Description                          |
|----------------|------------|--------------------------------------|
| `provider`     | `str`      | Nom du fournisseur de stemmer        |
| `language`     | `str`      | Code de langue                       |
| `total_words`  | `int`      | Nombre total de mots de test         |
| `successful`   | `int`      | Mots stemmés avec succès             |
| `failed`       | `int`      | Mots qui ont échoué                  |
| `results`      | `list[dict]` | Résultats par mot avec `word`, `stemmed`, `success` |

## Intégration avec StemmingMiddleware

Les fournisseurs de stemmers peuvent être utilisés avec le `StemmingMiddleware` de `whoosh_modern.middleware.analyzer` :

```python
from whoosh_modern.analysis.stemmer_providers import get_stemmer
from whoosh_modern.middleware.analyzer import StemmingMiddleware

stemmer = get_stemmer("auto", "english")
middleware = StemmingMiddleware(
    stemmer=stemmer.stem,
    fields=["title", "content"],  # Ne stemmer que ces champs
    stem_query=True,              # Also stemmer la requête de recherche
)
```

## Migration depuis Whoosh Classique

### Ancienne API (Whoosh 1.x/2.x)

```python
from whoosh.analysis import StemmingAnalyzer as OldAnalyzer
analyzer = OldAnalyzer("en")  # Codé en dur sur "english"
```

### Nouvelle API (Whoosh-NG 2.0)

```python
from whoosh_modern.analysis import StemmingAnalyzer

# Détection automatique du backend (recommandé)
analyzer = StemmingAnalyzer("auto", language="en")

# Ou utiliser un analyseur linguistique
from whoosh_modern.linguistics.stemmers import EnglishAnalyzer
analyzer = EnglishAnalyzer()
```

> **Note** : L'ancienne `StemmingAnalyzer("en")` était codée en dur sur la langue `"english"`. La nouvelle `StemmingAnalyzer(stemmer, language)` est explicite et prend en charge toutes les langues Snowball via PyStemmer.

## Installation

```bash
# Sans PyStemmer (utilise le stemmer interne, plus lent)
pip install whoosh-ng

# Avec PyStemmer (recommandé, plus rapide)
pip install whoosh-ng[fast-stemming]

# Analyse moderne complète
pip install whoosh-ng[modern]
```

## Voir Aussi

- [Guide Stemming et Mots Vides](stemming.md) — Guide classique de stemming de Whoosh
- [Guide Synonymes & Linguistique](linguistics-sprint-d.md) — Moteur d'expansion de synonymes
- [API: Moderne](../api/modern.md) — Référence complète de l'API pour les extensions d'analyse
