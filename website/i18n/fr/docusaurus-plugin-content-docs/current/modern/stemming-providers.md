---
title: "Providers de Stemmers"
sidebar_position: 53
---

# Providers de Stemmers

Module : `whoosh_modern.analysis.stemmer_providers`, `whoosh_modern.analysis.stemming_analyzer`, `whoosh_modern.linguistics.stemmers`
Version : 2.0.0

Le système de providers de stemmers vous donne un contrôle flexible sur le
backend de stemming utilisé pour l'analyse de texte. Il prend en charge
l'auto-détection, la sélection explicite de backend et l'enregistrement de
stemmers personnalisés — le tout avec une API propre de style plugin.

## Aperçu du module

```text
whoosh_modern.analysis
    ├── stemmer_providers.py   # Protocole StemmerProvider, backends Internal/PyStemmer, register_stemmer, get_stemmer
    └── stemming_analyzer.py   # StemmingAnalyzer enrichi avec support de plugins

whoosh_modern.linguistics.stemmers
    └── __init__.py            # Analyseurs spécifiques à une langue (FR/EN/DE/ES/IT)
```

## Protocole StemmerProvider

Localisé dans `whoosh_modern.analysis.stemmer_providers` :

```python
from whoosh_modern.analysis.stemmer_providers import StemmerProvider

class MyStemmer(StemmerProvider):
    def stem(self, word: str) -> str:
        """Stem un seul mot."""
        ...

    @property
    def name(self) -> str:
        """Renvoie le nom du stemmer."""
        return "my_stemmer"

    @property
    def language(self) -> str:
        """Renvoie le code de langue."""
        return "english"
```

## Obtenir un stemmer

### Auto-détection (recommandée)

La fonction `get_stemmer("auto", language)` sélectionne automatiquement le
meilleur backend disponible :

```python
from whoosh_modern.analysis.stemmer_providers import get_stemmer

# Auto-détecte : privilégie PyStemmer si installé, repli sur le stemmer interne
stemmer = get_stemmer("auto", "english")
print(stemmer.stem("running"))  # "run"
print(stemmer.name)             # "pystemmer" ou "internal"
```

**Ordre de priorité :**
1. **PyStemmer** (le plus rapide, nécessite `pip install whoosh-ng[fast-stemming]`)
2. **Stemmer interne** (Porter stemmer intégré, toujours disponible)

### Sélection explicite du backend

```python
from whoosh_modern.analysis.stemmer_providers import get_stemmer

# Force le stemmer interne
stemmer = get_stemmer("internal", "english")

# Force PyStemmer (nécessite l'installation)
stemmer = get_stemmer("pystemmer", "english")
```

### Lister les backends disponibles

```python
from whoosh_modern.analysis.stemmer_providers import list_available_backends

backends = list_available_backends()
print(backends)
# {'internal': 'available', 'pystemmer': 'available', 'my_custom': 'registered'}
```

| Backend     | Chaîne de statut    | Nécessite                          |
|-------------|---------------------|------------------------------------|
| `internal`  | `"available"`       | Aucun (toujours fourni)            |
| `pystemmer` | `"available"` / `"not installed"` | `pip install whoosh-ng[fast-stemming]` |
| Custom      | `"registered"`      | Enregistré via `@register_stemmer` |

## Providers de stemmers intégrés

### InternalStemmerProvider

Encapsule le Porter stemmer intégré de Whoosh. Toujours disponible (aucune
dépendance supplémentaire) :

```python
from whoosh_modern.analysis.stemmer_providers import InternalStemmerProvider

stemmer = InternalStemmerProvider("english")
print(stemmer.stem("cats"))    # "cat"
print(stemmer.stem("running")) # "run"
```

### PyStemmerProvider

Encapsule la bibliothèque `Stemmer` pour un stemming haute performance. Prend en
charge toutes les langues Snowball :

```python
from whoosh_modern.analysis.stemmer_providers import PyStemmerProvider

# Nécessite : pip install whoosh-ng[fast-stemming]
stemmer = PyStemmerProvider("english")
print(stemmer.stem("cats"))    # "cat"
```

**Note** : ce provider appelle `self._stemmer.stemWord(word)` pour stemmer les
mots. Assurez-vous que PyStemmer est installé, sinon l'auto-détection repliera
sur le stemmer interne.

### IdentityStemmerProvider

Un stemmer sans effet pour les tests ou quand le stemming n'est pas souhaité :

```python
from whoosh_modern.analysis.stemmer_providers import IdentityStemmerProvider

stemmer = IdentityStemmerProvider()
print(stemmer.stem("anything"))  # "anything"
```

## Enregistrer un stemmer personnalisé

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

# Utilisez-le maintenant
from whoosh_modern.analysis.stemmer_providers import get_stemmer

stemmer = get_stemmer("simple", "english")
print(stemmer.stem("cats"))  # "cat"
```

## StemmingAnalyzer (enrichi)

Localisé dans `whoosh_modern.analysis.stemming_analyzer`, c'est le point d'entrée
principal pour créer des analyseurs conscient de la langue :

```python
from whoosh_modern.analysis import StemmingAnalyzer

# Auto-détecte le meilleur stemmer pour l'anglais
analyzer = StemmingAnalyzer(stemmer="auto", language="english")

# Stemmer interne explicite
analyzer = StemmingAnalyzer(stemmer="internal", language="english")

# Backend PyStemmer (si installé)
analyzer = StemmingAnalyzer(stemmer="pystemmer", language="french")

# Provider de stemmer personnalisé
analyzer = StemmingAnalyzer(stemmer=my_stemmer_instance)
```

### Paramètres de StemmingAnalyzer

| Paramètre   | Type                          | Défaut                  | Description                      |
|-------------|-------------------------------|-------------------------|----------------------------------|
| `expression`| Motif regex                  | motif de token par défaut | Regex de tokenization          |
| `stoplist`  | Itérable de mots vides       | `whoosh.analysis.STOP_WORDS` | Mots vides à filtrer       |
| `minsize`   | `int`                         | `2`                     | Longueur minimale des tokens    |
| `maxsize`   | `int \| None`                 | `None`                  | Longueur maximale des tokens    |
| `gaps`      | `bool`                        | `False`                 | Découpe sur l'expression vs. le match |
| `stemmer`   | `str \| StemmerProvider`      | `"auto"`                | Backend de stemming             |
| `language`  | `str`                         | `"english"`             | Code de langue                  |
| `ignore`    | `set[str] \| None`            | `None`                  | Mots à ignorer                  |
| `cachesize` | `int`                         | `50000`                 | Taille du cache de stemming     |

### Utilisation avec les types de champs

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

## Analyseurs spécifiques à une langue

Analyseurs préconstruits pour cinq langues, disponibles dans
`whoosh_modern.linguistics.stemmers` :

```python
from whoosh_modern.linguistics.stemmers import (
    EnglishAnalyzer,
    FrenchAnalyzer,
    GermanAnalyzer,
    SpanishAnalyzer,
    ItalianAnalyzer,
)

# Chacun est appelable et renvoie une liste de tokens
en = EnglishAnalyzer()
tokens = en("The quick brown foxes")
# tokens sont stemmés : ["quick", "brown", "fox"] (mots vides comme "the" supprimés)
```

### Analyseurs de langue disponibles

| Classe             | Langue   | Module                              |
|--------------------|----------|-------------------------------------|
| `EnglishAnalyzer`  | Anglais  | `whoosh_modern.linguistics.stemmers` |
| `FrenchAnalyzer`   | Français | `whoosh_modern.linguistics.stemmers` |
| `GermanAnalyzer`   | Allemand | `whoosh_modern.linguistics.stemmers` |
| `SpanishAnalyzer`  | Espagnol | `whoosh_modern.linguistics.stemmers` |
| `ItalianAnalyzer`  | Italien  | `whoosh_modern.linguistics.stemmers` |

Chacun utilise en interne `get_stemmer("auto", language)` pour sélectionner le
meilleur backend disponible et applique les mots vides spécifiques à la langue.

## Validation de compatibilité des stemmers

Validez qu'un provider de stemmer fonctionne correctement avec un ensemble de
mots de test :

```python
from whoosh_modern.analysis.stemmer_providers import (
    get_stemmer,
    validate_stemmer_compatibility,
)

stemmer = get_stemmer("auto", "english")
report = validate_stemmer_compatibility(stemmer, ["running", "cats", "jumps", "houses"])

print(report["total_words"])   # 4
print(report["successful"])    # 4 (ou moins en cas d'erreur)
print(report["failed"])        # 0
print(report["results"])       # [{'word': 'running', 'stemmed': 'run', 'success': True}, ...]
```

### Structure du rapport de compatibilité

| Champ         | Type       | Description                          |
|---------------|------------|--------------------------------------|
| `provider`    | `str`      | Nom du provider de stemming          |
| `language`    | `str`      | Code de langue                       |
| `total_words` | `int`      | Nombre total de mots de test         |
| `successful`  | `int`      | Mots stemmés avec succès             |
| `failed`      | `int`      | Mots en échec                        |
| `results`     | `list[dict]` | Résultats par mot avec `word`, `stemmed`, `success` |

## Intégration avec StemmingMiddleware

Les providers de stemmers peuvent être utilisés avec le `StemmingMiddleware`
depuis `whoosh_modern.middleware.analyzer` :

```python
from whoosh_modern.analysis.stemmer_providers import get_stemmer
from whoosh_modern.middleware.analyzer import StemmingMiddleware

stemmer = get_stemmer("auto", "english")
middleware = StemmingMiddleware(
    stemmer=stemmer.stem,
    fields=["title", "content"],  # Stemme uniquement ces champs
    stem_query=True,              # Stemme aussi la requête de recherche
)
```

## Migration depuis le Whoosh classique

### Ancienne API (Whoosh 1.x/2.x)

```python
from whoosh.analysis import StemmingAnalyzer as OldAnalyzer
analyzer = OldAnalyzer("en")  # Code en dur sur "english"
```

### Nouvelle API (Whoosh-NG 2.0)

```python
from whoosh_modern.analysis import StemmingAnalyzer

# Auto-détecte le backend (recommandé)
analyzer = StemmingAnalyzer("auto", language="en")

# Ou utilisez un analyseur spécifique à une langue
from whoosh_modern.linguistics.stemmers import EnglishAnalyzer
analyzer = EnglishAnalyzer()
```

> **Note** : l'ancien `StemmingAnalyzer("en")` codait en dur la langue sur
> `"english"`. Le nouveau paramètre `StemmingAnalyzer(stemmer, language)` est
> explicite et prend en charge toutes les langues Snowball via PyStemmer.

## Installation

```bash
# Sans PyStemmer (utilise le stemmer interne, plus lent)
pip install whoosh-ng

# Avec PyStemmer (recommandé, plus rapide)
pip install whoosh-ng[fast-stemming]

# Analyse moderne complète
pip install whoosh-ng[modern]
```

## Intégration des providers de stemming dans le pipeline

Le système `StemmerProvider` s'intègre à **deux niveaux** : les analyseurs de
niveau champ et le middleware de pipeline. Comprendre les deux est essentiel
pour éviter le double stemming.

### Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│  StemmingAnalyzer (niveau champ, dans le Schema)                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ RegexTokenizer() │ StopFilter │ StemmingAnalyzer          │  │
│  │                    (mots vides)   │                       │  │
│  │                                   ▼                       │  │
│  │                         stemfn = provider.stem            │  │
│  │                                   │                       │  │
│  │                                   ▼                       │  │
│  │                         Token(stemmed=True)                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Appliqué par le cœur de Whoosh à l'indexation ET à la recherche  │
│  (via QueryParser). Automatique, aucun middleware nécessaire.     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  StemmingMiddleware (niveau pipeline)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ before_index(context)                                     │  │
│  │   └── stemme toutes les valeurs str dans context.document │  │
│  │                                                             │  │
│  │ before_search(context)                                     │  │
│  │   └── stemme context.query si stem_query=True             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Accroché à la MiddlewareChain. Opt-in manuel.                  │
└─────────────────────────────────────────────────────────────────┘
```

### Niveau 1 : niveau champ (automatique)

Le `StemmingAnalyzer` encapsule le `StemmingAnalyzer` intégré de Whoosh et
injecte la méthode `.stem` d'un `StemmerProvider` comme `stemfn`. Le cœur de
Whoosh l'applique automatiquement au champ à l'indexation et à la recherche.

```python
from whoosh.fields import Schema, TEXT
from whoosh_modern.analysis import StemmingAnalyzer, get_stemmer

# Auto-détecte le meilleur stemmer (PyStemmer privilégié)
stemmer = get_stemmer("auto", "english")

# Crée l'analyseur avec la fonction de stemming du provider
analyzer = StemmingAnalyzer(stemmer=stemmer)

schema = Schema(
    title=TEXT(stored=True),
    content=TEXT(analyzer=analyzer),
)

# À l'indexation : "running cats" → ["run", "cat"]
# À la recherche : QueryParser utilise aussi le même analyseur
# donc "running cats" correspond aux documents contenant "run cat"
```

**Avantages** : automatique, aucune configuration de middleware requise,
comportement index/requête cohérent.

**Inconvénients** : nécessite de définir l'analyseur sur chaque champ `TEXT`.
Plus difficile à modifier à l'exécution.

### Niveau 2 : niveau middleware (opt-in)

`StemmingMiddleware` applique le stemming au niveau du pipeline, opérant sur
les valeurs chaîne brutes dans `context.document` et `context.query` avant que
les analyseurs de Whoosh ne les voient.

```python
from whoosh_modern.middleware import StemmingMiddleware
from whoosh_modern.analysis import get_stemmer
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.wrappers import MiddlewareWriter

stemmer = get_stemmer("auto", "english")

chain = MiddlewareChain([
    StemmingMiddleware(
        stemmer=stemmer.stem,
        fields=["title", "content"],  # None = tous les champs str
        stem_query=True,
    ),
])

with MiddlewareWriter(ix.writer(), chain) as writer:
    writer.add_document(title="Running cats", content="Fast dogs")
    # before_index stemme : "Running cats" → "run cat"
    writer.commit()
```

**Avantages** : fonctionne sur n'importe quel champ sans modifier le schéma.
Peut être activé/désactivé à l'exécution.

**Inconvénients** : doit être câblé manuellement dans le pipeline. Risque de
double stemming si le champ utilise aussi `StemmingAnalyzer`.

### Exemple de pipeline complet : index + recherche

```python
from whoosh import index, fields
from whoosh.qparser import QueryParser
from whoosh_modern.analysis import StemmingAnalyzer, get_stemmer
from whoosh_modern.middleware import StemmingMiddleware
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.wrappers import MiddlewareWriter, MiddlewareSearcher

# 1. Schéma avec analyseur de niveau champ
stemmer = get_stemmer("auto", "english")
schema = fields.Schema(
    title=fields.TEXT(stored=True, analyzer=StemmingAnalyzer(stemmer=stemmer)),
    content=fields.TEXT(analyzer=StemmingAnalyzer(stemmer=stemmer)),
)

ix = index.create_in("indexdir", schema)

# 2. Index avec middleware (pas de double stemming car
#    on n'utilise pas StemmingMiddleware quand les champs ont déjà StemmingAnalyzer)
with ix.writer() as writer:
    writer.add_document(title="Running cats", content="Fast dogs")
    writer.commit()

# 3. Recherche : QueryParser applique le même analyseur à la requête
with ix.searcher() as searcher:
    qp = QueryParser("content", schema)
    q = qp.parse("running cats")
    results = searcher.search(q)
    # "running" est stemmé en "run" par l'analyseur
    # "cats" est stemmé en "cat" par l'analyseur
    # Correspond au document contenant "run" et "cat"
```

### Éviter le double stemming

```python
# FAUX : double stemming
schema = Schema(
    content=TEXT(analyzer=StemmingAnalyzer(stemmer="auto")),
)
chain = MiddlewareChain([
    StemmingMiddleware(stemmer=get_stemmer("auto").stem),  # À ne pas faire !
])
# Résultat : "running" → "run" (analyseur) → "run" (middleware) — inoffensif mais gaspilleur

# CORRECT : choisissez UN seul niveau
# Option A : niveau champ uniquement (recommandé pour les schémas statiques)
schema = Schema(content=TEXT(analyzer=StemmingAnalyzer(stemmer="auto")))
# Aucun StemmingMiddleware nécessaire

# Option B : middleware uniquement (pour les champs dynamiques)
schema = Schema(content=TEXT)  # Pas d'analyseur
chain = MiddlewareChain([StemmingMiddleware(stemmer=get_stemmer("auto").stem)])
```

### Provider de stemmer personnalisé

```python
from whoosh_modern.analysis import register_stemmer, get_stemmer

@register_stemmer("my_stemmer")
class MyStemmer:
    def stem(self, word: str) -> str:
        return word.lower().rstrip("s")

# Utilisez-le comme n'importe quel backend intégré
stemmer = get_stemmer("my_stemmer", "english")
analyzer = StemmingAnalyzer(stemmer=stemmer)
```

## Voir aussi

- [Guide Stemming et Mots Vides](../core/stemming.md) — Guide classique de stemming de Whoosh
- [Guide Synonymes & Linguistique](linguistics.md) — Moteur d'expansion de synonymes
- [Guide d'Intégration des Providers](provider-integration.md) — Guide complet du pipeline pour tous les providers
- [API : Linguistique](../api/modern.md) — Référence complète de l'API pour les extensions d'analyse
