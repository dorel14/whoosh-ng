---
title: "Synonymes & Linguistique"
sidebar_position: 52
---

# Synonymes & Linguistique

Module : `whoosh_modern.linguistics.synonyms`, `whoosh_modern.linguistics.stemmers`
Version : 2.0.0

Le module de linguistique fournit un moteur complet d'expansion de synonymes
et des analyseurs de texte spécifiques à une langue. Il s'intègre au pipeline de
middleware pour étendre les requêtes et les documents avec des synonymes aussi
bien à l'indexation qu'à la recherche.

## Aperçu du module

```text
whoosh_modern.linguistics
    ├── synonyms/
    │   ├── provider.py       # Protocole SynonymProvider + StaticSynonymProvider
    │   ├── yaml_provider.py  # YAMLSynonymProvider
    │   ├── json_provider.py  # JSONSynonymProvider
    │   ├── store.py          # SQLiteSynonymStore
    │   ├── compiler.py       # SynonymCompiler
    │   ├── manager.py        # SynonymManager
    │   ├── middleware.py      # SynonymExpansionMiddleware
    │   └── languages.py      # LANG_SYNONYMS (FR/EN/DE/ES/IT)
    └── stemmers/
        └── __init__.py       # Analyseurs spécifiques à une langue (FR/EN/DE/ES/IT)
```

## Providers de synonymes

### SynonymProvider (Protocole)

Le protocole de base implémenté par tous les providers de synonymes :

```python
from whoosh_modern.linguistics.synonyms import SynonymProvider

class MyProvider(SynonymProvider):
    def get_synonyms(self, word: str) -> list[str]:
        """Renvoie les synonymes du mot donné."""
        ...

    def add_synonym(self, word: str, synonyms: list[str]) -> None:
        """Ajoute des synonymes au mot donné."""
        ...

    def remove_synonym(self, word: str, synonym: str) -> None:
        """Retire un synonyme du mot donné."""
        ...
```

### StaticSynonymProvider

Provider en mémoire appuyé sur un dictionnaire :

```python
from whoosh_modern.linguistics.synonyms import StaticSynonymProvider

provider = StaticSynonymProvider({
    "car": ["automobile", "vehicle", "auto"],
    "house": ["home", "residence"],
})

print(provider.get_synonyms("car"))  # ['automobile', 'vehicle', 'auto']
```

### YAMLSynonymProvider

Charge les synonymes depuis un fichier YAML :

```yaml
# synonyms.yaml
car:
  - automobile
  - vehicle
  - auto
house:
  - home
  - residence
```

```python
from whoosh_modern.linguistics.synonyms import YAMLSynonymProvider

# Nécessite : pip install pyyaml
provider = YAMLSynonymProvider("synonyms.yaml")
print(provider.get_synonyms("car"))  # ['automobile', 'vehicle', 'auto']
```

### JSONSynonymProvider

Charge les synonymes depuis un fichier JSON :

```json
{
    "car": ["automobile", "vehicle", "auto"],
    "house": ["home", "residence"]
}
```

```python
from whoosh_modern.linguistics.synonyms import JSONSynonymProvider

provider = JSONSynonymProvider("synonyms.json")
print(provider.get_synonyms("car"))
```

### SQLiteSynonymStore

Stockage persistant de synonymes appuyé sur SQLite :

```python
from whoosh_modern.linguistics.synonyms import SQLiteSynonymStore

store = SQLiteSynonymStore("synonyms.db")

# Opérations CRUD
store.add_synonym("car", ["automobile", "vehicle"])
print(store.get_synonyms("car"))  # ['automobile', 'vehicle']
store.remove_synonym("car", "automobile")
print(store.get_synonyms("car"))  # ['vehicle']
store.close()
```

### SynonymCompiler

Précompile les données de synonymes brutes dans un format de recherche rapide :

```python
from whoosh_modern.linguistics.synonyms import SynonymCompiler

compiler = SynonymCompiler({"car": ["automobile", "vehicle"]})
compiler.add("house", ["home", "residence"])
compiler.merge({"book": ["publication", "work"]})

compiled = compiler.compile()
print(compiled)
# {'car': ['automobile', 'vehicle'], 'house': ['home', 'residence'], 'book': ['publication', 'work']}
```

## SynonymManager

Le `SynonymManager` est l'interface de haut niveau pour gérer les synonymes. Il
encapsule en interne un `StaticSynonymProvider` et prend en charge
l'import/export :

```python
from whoosh_modern.linguistics.synonyms import SynonymManager

manager = SynonymManager({"car": ["automobile", "vehicle"]})

# CRUD
manager.add_synonyms("house", ["home", "residence"])
print(manager.get_synonyms("house"))  # ['home', 'residence']
manager.remove_synonym("house", "home")

# Import depuis des sources externes
manager.import_yaml("synonyms.yaml")   # Nécessite PyYAML
manager.import_json("synonyms.json")

# Export
manager.export_json("output.json")
```

### Workflow d'import/export

```python
# Import depuis YAML
manager = SynonymManager()
manager.import_yaml("my_synonyms.yaml")

# Export vers JSON (ex : pour migration ou sauvegarde)
manager.export_json("backup.json")
```

## Dictionnaires de synonymes préconstruits

Le dictionnaire `LANG_SYNONYMS` contient des correspondances de synonymes de
démarrage pour cinq langues :

```python
from whoosh_modern.linguistics.synonyms import LANG_SYNONYMS

# Langues disponibles : fr, en, de, es, it
french_syns = LANG_SYNONYMS["fr"]
print(french_syns["voiture"])  # ['automobile', 'véhicule']

english_syns = LANG_SYNONYMS["en"]
print(english_syns["car"])  # ['automobile', 'vehicle']

# Amorce un SynonymManager avec une langue
manager = SynonymManager(LANG_SYNONYMS["fr"])
```

| Langue  | Code | Entrée d'exemple                          |
|---------|------|-------------------------------------------|
| Français | `fr` | `"voiture": ["automobile", "véhicule"]`    |
| Anglais | `en` | `"car": ["automobile", "vehicle"]`        |
| Allemand | `de` | `"auto": ["wagen", "fahrzeug"]`           |
| Espagnol | `es` | `"coche": ["automóvil", "vehículo"]`      |
| Italien | `it` | `"auto": ["automobile", "veicolo"]`       |

> **Note** : il s'agit de dictionnaires de démarrage minimaux destinés à la
> démonstration. Les déploiements en production devraient charger des sources
> organisées ou spécifiques à un domaine.

## SynonymExpansionMiddleware

Intègre l'expansion de synonymes dans le pipeline de middleware. Il étend à la
fois les requêtes de recherche et les champs de documents indexés :

```python
from whoosh_modern.linguistics.synonyms import (
    SynonymManager,
    SynonymExpansionMiddleware,
)

# Crée un manager avec vos synonymes
manager = SynonymManager({
    "car": ["automobile", "vehicle"],
    "house": ["home", "residence"],
})

# Crée le middleware
middleware = SynonymExpansionMiddleware(manager)

# Enregistre auprès du PluginManager ou de la MiddlewareChain
from whoosh.plugins.manager import PluginManager
PluginManager._default.register_middleware("synonym", middleware)
```

### Fonctionnement

- **`before_search`** : étend `context.query` en ajoutant les synonymes de
  chaque token
- **`before_index`** : étend les valeurs chaîne dans `context.document` en
  ajoutant les synonymes

```python
# Avant : query = "car"
# Après  : query = "car automobile vehicle"

# Avant : document = {"title": "house for sale"}
# Après : document = {"title": "house for sale home residence"}
```

## Analyseurs de stemming spécifiques à une langue

Localisés dans `whoosh_modern.linguistics.stemmers`, ces analyseurs combinent
tokenization, stemming et suppression des mots vides :

```python
from whoosh_modern.linguistics.stemmers import (
    EnglishAnalyzer,
    FrenchAnalyzer,
    GermanAnalyzer,
    SpanishAnalyzer,
    ItalianAnalyzer,
)

# Chaque analyseur est une instance de LanguageAnalyzer et est appelable :
# il renvoie une liste de tokens
analyzer = EnglishAnalyzer
tokens = analyzer("The running cats")
# tokens sont stemmés : ["run", "cat"] (mots vides supprimés)

# L'usage "style classe" rétro-compatible fonctionne aussi : appeler l'analyseur
# sans argument renvoie une nouvelle instance, donc le code historique
# écrit comme EnglishAnalyzer()(text) continue de fonctionner inchangé.
tokens = EnglishAnalyzer()("The running cats")
```

### Sélection du backend de stemming

Sous le capot, les stemmers utilisent `whoosh_modern.analysis.stemmer_providers`
:

```python
from whoosh_modern.analysis.stemmer_providers import (
    get_stemmer,
    register_stemmer,
    list_available_backends,
)

# Auto-détecte le meilleur stemmer disponible (PyStemmer privilégié)
stemmer = get_stemmer("auto", "english")

# Backend explicite
stemmer = get_stemmer("internal", "english")   # Stemmer intégré de Whoosh
stemmer = get_stemmer("pystemmer", "english")   # PyStemmer (plus rapide)

# Liste les backends disponibles
print(list_available_backends())
# {'internal': 'available', 'pystemmer': 'available', ...}

# Enregistre un stemmer personnalisé
@register_stemmer("my_stemmer")
class MyStemmer:
    def stem(self, word: str) -> str:
        return word.lower()
```

| Backend     | Nécessite                       | Vitesse                |
|-------------|---------------------------------|------------------------|
| `auto`      | Aucun (repli automatique)       | Le plus rapide dispo.  |
| `internal`  | Aucun (Porter stemmer intégré)   | Moyenne                |
| `pystemmer` | `pip install whoosh-ng[fast-stemming]` | Rapide         |

## Exemple d'intégration : pipeline complet

```python
from whoosh_modern.linguistics import (
    EnglishAnalyzer,
    LANG_SYNONYMS,
    SynonymExpansionMiddleware,
    SynonymManager,
)
from whoosh.middleware.chain import MiddlewareChain
from whoosh.middleware.wrappers import MiddlewareWriter, MiddlewareSearcher

# 1. Construit le manager de synonymes avec les synonymes anglais
syn_manager = SynonymManager(LANG_SYNONYMS["en"])
syn_manager.add_synonyms("search", ["query", "find", "lookup"])

# 2. Crée le middleware d'expansion de synonymes
syn_middleware = SynonymExpansionMiddleware(syn_manager)

# 3. Construit la chaîne de middleware
chain = MiddlewareChain([syn_middleware])

# 4. Enveloppe le writer et le searcher
with MiddlewareWriter(ix.writer(), chain) as writer:
    writer.add_document(title="How to search in Whoosh")

with MiddlewareSearcher(ix.searcher(), chain) as searcher:
    # La requête "search" est étendue en "search query find lookup"
    results = searcher.search("search")
```

## Registre de langues

`LanguageRegistry` mappe les codes de langue vers des instances `LanguageProfile`, centralisant la résolution d'analyzer, de stemmer, de provider de synonymes et de détecteur de langue.

```python
from whoosh_modern.linguistics.registry import (
    LanguageRegistry,
    LanguageProfile,
    StemmerRegistry,
    get_default_registry,
)

# Utilise le registry pré-peuplé par défaut (FR/EN/DE/ES/IT)
registry = get_default_registry()

# Résout un profil de langue
profile = registry.resolve("fr")
print(profile.language)   # "fr"
print(profile.analyzer)   # instance de FrenchAnalyzer

# Enregistre un profil de langue personnalisé
custom = LanguageProfile(
    language="pt",
    analyzer=...,  # votre analyzer
    stemmer=...,   # votre stemmer
)
registry.register(custom)

# StemmerRegistry ajoute des helpers spécifiques aux stemmers
stem_registry = StemmerRegistry(registry._profiles.values())
stemmer = stem_registry.get_stemmer("fr")
```

## Analyseur multilingue

`MultiLanguageAnalyzer` applique plusieurs analyseurs de langue simultanément pour l'indexation multilingue.

```python
from whoosh_modern.linguistics.analyzers import MultiLanguageAnalyzer

# Par défaut : FR/EN/DE/ES/IT
analyzer = MultiLanguageAnalyzer()

# Ensemble de langues personnalisé
analyzer = MultiLanguageAnalyzer(languages=["fr", "en"])

tokens = analyzer("hello bonjour")
# Retourne les tokens combinés de tous les analyseurs configurés
```

## Auto-détection de langue

`StopwordDetector` et `LangDetectProvider` permettent la détection automatique de langue :

```python
from whoosh_modern.linguistics.detection import StopwordDetector

detector = StopwordDetector(supported_languages=["fr", "en", "de"])
lang = detector.detect("Ceci est un texte en français")
print(lang)  # "fr"
```

Utilisation avec `SearchApplication` pour la résolution automatique de langue :

```python
from whoosh_modern import SearchApplication
from whoosh_modern.linguistics.detection import StopwordDetector

app = SearchApplication(
    source=my_source,
    language_detector=StopwordDetector(),
)

# FieldConfig supporte language="auto"
# Le détecteur résout la langue par document
```

## Analyseur Explain

`ExplainAnalyzer` expose le pipeline de tokenization/stemming pour Search Studio :

```python
from whoosh_modern.linguistics.explain import ExplainAnalyzer

explainer = ExplainAnalyzer(EnglishAnalyzer)
result = explainer.explain("The running cats")

print(result.text)       # "The running cats"
print(result.tokens)     # ["run", "cat"]
```

## Débogage d'analyse avec ExplainAnalyzer

`ExplainAnalyzer` encapsule n'importe quel analyseur existant et retourne une
`AnalysisExplanation` décrivant comment un texte est transformé. C'est un outil
utile pour déboguer des chaînes d'analyseurs complexes, surtout lors de l'utilisation
d'analyseurs multilingues, de filtres stopwords ou de remplacements de stemming
par dictionnaire.

```python
from whoosh_modern.linguistics.explain import ExplainAnalyzer
from whoosh.analysis import StandardAnalyzer

explainer = ExplainAnalyzer(StandardAnalyzer())
explanation = explainer.explain(
    "A quick brown fox jumps over the lazy dog"
)

print(f"Texte original : {explanation.text}")
print(f"Tokens finaux : {explanation.tokens}")

print("\nExplications étape par étape :")
for step in explanation.explanations:
    print(
        f"  - {step.step} : '{step.original}' -> '{step.result}'"
    )
```

Exemple de sortie :

```text
Texte original : A quick brown fox jumps over the lazy dog
Tokens finaux : ['quick', 'brown', 'fox', 'jumps', 'lazy', 'dog']

Explications étape par étape :
  - tokenize : 'A' -> 'A'
  - lowercase : 'A' -> 'a'
  - stop : 'a' -> ''
  - tokenize : 'quick' -> 'quick'
  - lowercase : 'quick' -> 'quick'
  ...
```

### Interprétation de la sortie

- `explanation.text` — le texte d'entrée original.
- `explanation.tokens` — la liste finale de tokens après toutes les étapes de l'analyseur.
- `explanation.explanations` — une liste chronologique d'objets
  `TokenExplanation` montrant chaque transformation.

Utilisez ceci lorsque :
- une chaîne d'analyseurs se comporte différemment de ce qui est attendu,
- vous avez besoin de vérifier quels stopwords ou règles de stemming sont appliqués,
- vous voulez comparer le comportement entre langues avec `MultiLanguageAnalyzer`.

## Override de stem par dictionnaire

Remplace le stemming Snowball par des dictionnaires métier :

```python
from whoosh_modern.linguistics.dictionary_stem_override import DictionaryStemOverride

override = DictionaryStemOverride({
    "voiture": "voitur",
    "maison": "maison",
})

print(override.stem("voiture"))  # "voitur"
print(override.stem("maison"))   # "maison"

# Ajoute des règles dynamiquement
override.add_rule("chien", "chien")
```

Utilisation avec `SearchApplication` :

```python
from whoosh_modern import SearchApplication

app = SearchApplication(
    source=my_source,
    dictionary_stem_overrides={"voiture": "voitur"},
)
```

## Analyseur de stemming avec cache

`CachedStemmingAnalyzer` encapsule les analyseurs de langue avec un cache LRU :

```python
from whoosh_modern.analysis.cached_stemming_analyzer import CachedStemmingAnalyzer
from whoosh_modern.linguistics.stemmers import FrenchAnalyzer

cached = CachedStemmingAnalyzer(FrenchAnalyzer, cache_size=50000)
tokens = cached("les maisons")
```

## Profileur de stemmer

Mesure l'impact du stemming sur le vocabulaire et les performances :

```python
from whoosh_modern.profiling.stemmer_profiler import StemmerProfiler

profiler = StemmerProfiler(stemmer=my_stemmer)
report = profiler.profile(["document 1", "document 2", ...])

print(report.original_tokens)        # Tokens totaux avant stemming
print(report.stemmed_tokens)         # Tokens uniques après stemming
print(report.reduction_ratio)        # Ratio de réduction du vocabulaire
print(report.estimated_size_reduction)  # Réduction estimée de la taille d'index %
print(report.avg_stem_time_ms)       # Temps moyen de stemming par token
```

## Préréglages d'analyseurs

Analyseurs préconfigurés pour des scénarios de recherche courants :

```python
from whoosh_modern.analysis.stemmer_presets import AnalyzerPresets

# Autocomplétion
autocomplete_analyzer = AnalyzerPresets.autocomplete()

# Correspondance partielle
partial_analyzer = AnalyzerPresets.partial_match()

# E-commerce
ecommerce_analyzer = AnalyzerPresets.ecommerce()

# Blog
blog_analyzer = AnalyzerPresets.blog()

# Multilingue
multilingual_analyzer = AnalyzerPresets.multilingual()

# Accès par nom
analyzer = AnalyzerPresets.get("autocomplete")
```

## Voir aussi

- [Synonymes](synonyms.md) — Providers de synonymes, manager et dictionnaires Wiktionary
- [Guide des Stemmers](stemming-providers.md) — Providers de stemming et analyseurs de langue
- [Guide du Middleware](middleware-pipeline.md) — Intégration du pipeline de middleware
- [Guide d'Intégration des Providers](provider-integration.md) — Guide complet du pipeline pour tous les providers
- [API : Linguistique](../api/modern.md) — Référence complète de l'API
