---
title: "Performance et Benchmarking"
nav_order: 61
permalink: /fr/guides/performance/
lang: fr
---

# Performance et Benchmarking

Whoosh-NG inclut un ensemble complet d'outils de benchmarking dans `whoosh_modern.profiling` pour mesurer et comparer les performances des analyseurs. Ce guide explique comment utiliser ces outils et documente les optimisations livrées dans la version 2.0.0.

## Démarrage rapide

```python
from whoosh_modern.profiling.benchmarks.regex_tokenizer import run_p5_1
from whoosh_modern.profiling.benchmarks.token_optimization import run_p5_2
from whoosh_modern.profiling.synthetic_datasets import SyntheticDatasetGenerator
from whoosh_modern.profiling.stemmer_benchmark import StemmerBenchmark

# Générer des datasets synthétiques pour des benchmarks cohérents
gen = SyntheticDatasetGenerator(seed=42)
datasets = gen.generate_all(count=5000)

# Exécuter le benchmark du tokeniseur (P5.1)
run_p5_1(datasets)

# Exécuter le benchmark de création de tokens (P5.2)
run_p5_2(token_count=100_000)

# Exécuter le benchmark du stemmer
bench = StemmerBenchmark()
bench.run(gen.generate_dataset("A", 5000))
print(bench.report())
```

## Outils de benchmarking

### SyntheticDatasetGenerator

Génère des datasets de texte déterministes de complexité variable :

```python
from whoosh_modern.profiling.synthetic_datasets import SyntheticDatasetGenerator

gen = SyntheticDatasetGenerator(seed=42)
datasets = gen.generate_all(count=5000)

# Dataset A: 2 tokens/doc (court)
# Dataset B: 50 tokens/doc (moyen)
# Dataset C: 500 tokens/doc (grand)
# Dataset D: 1200 tokens/doc (très grand)
for name, texts in datasets.items():
    print(f"{name}: {len(texts)} documents")
```

### P5.1 : Benchmark du RegexTokenizer

Compare différentes implémentations de tokeniseur :

```python
from whoosh_modern.profiling.benchmarks.regex_tokenizer import run_p5_1

results = run_p5_1(datasets)

# Compare :
# - Current Regex (whoosh par défaut)
# - Compiled Global regex
# - Manual Python tokenizer
# - C extension (re2, si disponible)
```

### P5.2 : Benchmark d'optimisation des tokens

Compare différentes implémentations d'objets Token :

```python
from whoosh_modern.profiling.benchmarks.token_optimization import run_p5_2

# Compare :
# - Current Token (dict-based)
# - __slots__ optimization
# - namedtuple
# - dataclass(slots=True)
results = run_p5_2(token_count=100_000)
```

### StemmerBenchmark

Compare les backends de stemming :

```python
from whoosh_modern.profiling.stemmer_benchmark import StemmerBenchmark

bench = StemmerBenchmark()
bench.run(texts, warmup=True)
print(bench.report())
# Résultats :
# Stemmer         Tokens/s        Time (s)    Tokens
# ------------------------------------------------------
# StemFilter      1,004,172       0.1503      150,983
# PyStemmer       ~2,100,000+     0.0719+     150,983
```

## Optimisations de performance

### Résumé des gains 2.0.0

| Optimisation | Composant | Gain mesurable |
|---|---|---|
| `__slots__` sur Token | `whoosh.analysis.acore` | +35% création de tokens |
| Regex globale compilée | `RegexTokenizer` | +50% débit regex |
| Postings compactés (1 posting) | `W3TermInfo` / `W3PostingsWriter` | +35% vitesse de commit |
| Postings compactés (2-8 postings) | `W3TermInfo` / `W3PostingsWriter` | +35% vitesse de commit |
| Cache de champ dans add_postings | `whoosh.codec.base` | -93% appels write_block |
| Encodage varint des positions | `whoosh.formats` | réduction de l'overhead par terme |
| Cache de stemmer | `whoosh.analysis.morph` | taux de hit 96,5 %, 4,12x sur champs répétitifs |
| Cache d'analyseur | `whoosh_modern.profiling.analyzer_cache` | 4,12x sur champs hautement répétitifs |
| Écrivain par lots | `whoosh_modern.indexing.batch_writer` | lots filtrés optimisés |
| Optimisation setdefault stopwords | `whoosh.formats` | réduction de l'overhead dict |

### Résultats de benchmark : 20 000 documents (`customers_csv`)

```
Avant :
  commit total      : 18,653 s
  analyzing         : 8,641 s  (51,5 %)
  committing        : 10,012 s  (27,1 %)
  write_postings    : 6,5 s
  write_block calls : ~72 612

Après :
  commit total      : 6,806 s  (-63,5 %)
  analyzing         : ~2,7 s   (-68 %)
  committing        : 6,806 s  (-32 %)
  write_postings    : 6,5 s -> allouations réduites
  write_block calls : 7 565   (-93 %)
  débit             : 1 275 docs/s
```

### Résultats de benchmark : Backends de stemming (1,5M de tokens)

| Stemmer | Débit | Relatif |
|---|---|---|
| StemFilter (interne) | 1 004 172 tokens/s | 1,0x |
| PyStemmer | ~2 100 000 tokens/s | ~2,1x |

### Résultats de benchmark : Tokeniseur regex

| Tokeniseur | Débit | Relatif |
|---|---|---|
| Current regex | ~1 000 000 tokens/s | 1,0x |
| Compiled global | ~2 300 000 tokens/s | 2,3x |

### Résultats de benchmark : Objet Token

| Implémentation | Tokens/s | Relatif |
|---|---|---|
| Current (dict) | 1 000 000 | 1,0x |
| `__slots__` | ~1 350 000 | 1,35x |

## Outils de profiling

### IndexingPipelineProfiler

Profile le pipeline d'indexation complet :

```python
from whoosh_modern.profiling.indexing_pipeline_profiler import IndexingPipelineProfiler

profiler = IndexingPipelineProfiler()
for doc in documents:
    profiler.before_tokenize(doc, analyzer)
    analyzer(doc)
    profiler.after_tokenize()

report = profiler.report()
print(report)
```

### CommitProfiler

Profile les performances de commit :

```python
from whoosh_modern.profiling.commit_profiler_v2 import CommitProfiler

profiler = CommitProfiler()
# ... indexer des documents ...
ix.commit()

report = profiler.report()
# Affiche : analyze, convert_fields, write_postings, flush, commit
```

### FieldIndexProfiler

Profile les coûts de conversion des champs :

```python
from whoosh_modern.profiling.field_index_profiler import FieldIndexProfiler

profiler = FieldIndexProfiler()
# ... indexer des documents ...
report = profiler.report()
```

### IndexQualityAnalyzer

Analyse les métriques de qualité de l'index :

```python
from whoosh_modern.profiling.index_quality_analyzer import IndexQualityAnalyzer

analyzer = IndexQualityAnalyzer(index_reader)
report = analyzer.analyze()
print(f"Termes singletons: {report['singleton_terms']}/{report['total_terms']} ({report['singleton_percent']}%)")
```

## Système de fournisseurs de stemmer

Whoosh-NG propose un système de fournisseurs de stemmer :

```python
from whoosh_modern.analysis import get_stemmer, StemmingAnalyzer, list_available_backends

# Vérifier les backends disponibles
print(list_available_backends())
# {'internal': 'available', 'pystemmer': 'not installed'}

# Utiliser la détection automatique (par défaut)
analyzer = StemmingAnalyzer(stemmer="auto")

# Stemmer interne explicite
analyzer = StemmingAnalyzer(stemmer="internal")

# PyStemmer (nécessite: pip install whoosh-ng[fast-stemming])
analyzer = StemmingAnalyzer(stemmer="pystemmer")
```

## Recommandations de performance

1. **Utilisez** `StemmingAnalyzer` de `whoosh_modern.analysis` pour une sélection automatique de PyStemmer
2. **Activez le cache de stemmer** pour le contenu répétitif (`cachesize=50000` par défaut)
3. **Minimisez les champs TEXT** — utilisez KEYWORD ou ID pour les champs à faible cardinalité
4. **Évitez les positions/chars stockés** sauf si la mise en évidence l'exige
5. **Utilisez l'indexation par lots** avec des segments plus grands pour de meilleurs débits
6. **Surveillez les termes singletons** — réduisez les termes rares via des listes de stopwords

## Exécution de la suite complète de benchmarks

```bash
cd whoosh-ng

# Exécuter tous les tests P5
uv run python -m pytest tests/test_regex_tokenizer_unicode.py tests/test_token_slots.py tests/test_stemmer_compatibility.py -v

# Suite de tests complète
uv run python -m pytest -q
```
