---
title: "Performance Benchmarking"
nav_order: 60
permalink: /en/guides/performance/
---

# Performance Benchmarking

Whoosh-NG includes a comprehensive benchmarking toolkit in `whoosh_modern.profiling` for measuring and comparing analyzer performance. This guide explains how to use these tools and documents the optimizations shipped in 2.0.0.

## Quick Start

```python
from whoosh_modern.profiling.benchmarks.regex_tokenizer import run_p5_1
from whoosh_modern.profiling.benchmarks.token_optimization import run_p5_2
from whoosh_modern.profiling.synthetic_datasets import SyntheticDatasetGenerator
from whoosh_modern.profiling.stemmer_benchmark import StemmerBenchmark

# Generate synthetic datasets for consistent benchmarks
gen = SyntheticDatasetGenerator(seed=42)
datasets = gen.generate_all(count=5000)

# Run tokenizer benchmark (P5.1)
run_p5_1(datasets)

# Run token creation benchmark (P5.2)
run_p5_2(token_count=100_000)

# Run stemmer benchmark
bench = StemmerBenchmark()
bench.run(gen.generate_dataset("A", 5000))
print(bench.report())
```

## Benchmarking Tools

### SyntheticDatasetGenerator

Generates deterministic text datasets of varying complexity:

```python
from whoosh_modern.profiling.synthetic_datasets import SyntheticDatasetGenerator

gen = SyntheticDatasetGenerator(seed=42)
datasets = gen.generate_all(count=5000)

# Dataset A: 2 tokens/doc (short)
# Dataset B: 50 tokens/doc (medium)
# Dataset C: 500 tokens/doc (large)
# Dataset D: 1200 tokens/doc (very large)
for name, texts in datasets.items():
    print(f"{name}: {len(texts)} documents")
```

### P5.1: RegexTokenizer Benchmark

Compares different tokenizer implementations:

```python
from whoosh_modern.profiling.benchmarks.regex_tokenizer import run_p5_1

results = run_p5_1(datasets)

# Compare:
# - Current Regex (whoosh default)
# - Compiled Global regex
# - Manual Python tokenizer
# - C extension (re2, if available)
```

### P5.2: Token Optimization Benchmark

Compares Token object implementations:

```python
from whoosh_modern.profiling.benchmarks.token_optimization import run_p5_2

# Compare:
# - Current Token (dict-based)
# - __slots__ optimization
# - namedtuple
# - dataclass(slots=True)
results = run_p5_2(token_count=100_000)
```

### StemmerBenchmark

Compares stemmer backends:

```python
from whoosh_modern.profiling.stemmer_benchmark import StemmerBenchmark

bench = StemmerBenchmark()
bench.run(texts, warmup=True)
print(bench.report())
# Output:
# Stemmer Benchmark
# ==================================================
# Stemmer         Tokens/s        Time (s)    Tokens
# ------------------------------------------------------
# StemFilter      1,004,172       0.1503      150,983
# PyStemmer       2,100,000+      0.0719+     150,983
```

## Performance Optimizations

### 2.0.0 Performance Summary

| Optimization | Component | Measurable Gain |
|---|---|---|
| `__slots__` on Token | `whoosh.analysis.acore` | +35% token creation |
| Global compiled regex | `RegexTokenizer` | +50% regex throughput |
| Compact postings (1-posting) | `W3TermInfo` / `W3PostingsWriter` | +35% commit speed |
| Compact postings (2-8 postings) | `W3TermInfo` / `W3PostingsWriter` | +35% commit speed |
| Field cache in add_postings | `whoosh.codec.base` | -93% write_block calls |
| Varint position encoding | `whoosh.formats` | reduced per-term overhead |
| Stemmer cache tuning | `whoosh.analysis.morph` | 96.5% hit rate, 4.12x on repetitive fields |
| Analyzer cache | `whoosh_modern.profiling.analyzer_cache` | 4.12x on high-repetition fields |
| Batch writer optimization | `whoosh_modern.indexing.batch_writer` | optimized filtered batches |
| Stopword setdefault optimization | `whoosh.formats` | reduced dict overhead |

### Benchmark Results: 20k Documents (`customers_csv`)

```
before:
  commit total      : 18.653s
  analyzing         : 8.641s  (51.5%)
  committing        : 10.012s (27.1%)
  write_postings    : 6.5s
  write_block calls : ~72612

after:
  commit total      : 6.806s   (-63.5%)
  analyzing         : ~2.7s    (-68%)
  committing        : 6.806s   (-32%)
  write_postings    : 6.5s -> reduced allocation
  write_block calls : 7565     (-93%)
  throughput        : 1275 docs/s
```

### Benchmark Results: Stemmer Backends (1.5M tokens)

| Stemmer | Throughput | Relative |
|---|---|---|
| StemFilter (internal) | 1,004,172 tokens/s | 1.0x |
| PyStemmer | ~2,100,000 tokens/s | ~2.1x |

### Benchmark Results: Regex Tokenizer

| Tokenizer | Throughput | Relative |
|---|---|---|
| Current regex | ~1,000,000 tokens/s | 1.0x |
| Compiled global | ~2,300,000 tokens/s | 2.3x |

### Benchmark Results: Token Object

| Implementation | Tokens/sec | Relative |
|---|---|---|
| Current (dict) | 1,000,000 | 1.0x |
| `__slots__` | ~1,350,000 | 1.35x |

## Profiling Tools

### IndexingPipelineProfiler

Profiles the complete indexing pipeline:

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

Profiles commit performance including field writing and posting flushing:

```python
from whoosh_modern.profiling.commit_profiler_v2 import CommitProfiler

profiler = CommitProfiler()
# ... index documents ...
ix.commit()

report = profiler.report()
# Shows: analyze, convert_fields, write_postings, flush, commit breakdown
```

### FieldIndexProfiler

Profiles field conversion costs:

```python
from whoosh_modern.profiling.field_index_profiler import FieldIndexProfiler

profiler = FieldIndexProfiler()
# ... index documents ...
report = profiler.report()
# Identifies expensive field types and conversion bottlenecks
```

### IndexQualityAnalyzer

Analyzes index quality metrics including singleton terms:

```python
from whoosh_modern.profiling.index_quality_analyzer import IndexQualityAnalyzer

analyzer = IndexQualityAnalyzer(index_reader)
report = analyzer.analyze()
print(f"Singleton terms: {report['singleton_terms']}/{report['total_terms']} ({report['singleton_percent']}%)")
```

## Stemmer Provider System

Whoosh-NG provides a pluggable stemmer provider system:

```python
from whoosh_modern.analysis import get_stemmer, StemmingAnalyzer, list_available_backends

# Check available backends
print(list_available_backends())
# {'internal': 'available', 'pystemmer': 'not installed'}

# Use auto-detection (default)
analyzer = StemmingAnalyzer(stemmer="auto")

# Explicit internal stemmer
analyzer = StemmingAnalyzer(stemmer="internal")

# PyStemmer (requires: pip install whoosh-ng[fast-stemming])
analyzer = StemmingAnalyzer(stemmer="pystemmer")

# Custom stemmer provider
from whoosh_modern.analysis.stemmer_providers import StemmerProvider

class MyStemmer(StemmerProvider):
    def __init__(self, language="english"):
        self._lang = language

    def stem(self, word):
        return word.lower()

    @property
    def name(self):
        return "my_stemmer"

    @property
    def language(self):
        return self._lang

analyzer = StemmingAnalyzer(stemmer=MyStemmer())
```

## Performance Recommendations

1. **Use `StemmingAnalyzer`** from `whoosh_modern.analysis` for automatic PyStemmer selection
2. **Enable stemmer cache** for repetitive content (`cachesize=50000` by default)
3. **Minimize TEXT fields** — use KEYWORD or ID for low-cardinality fields
4. **Avoid stored positions/chars** unless highlighting requires them
5. **Use batch indexing** with larger segments for better throughput
6. **Monitor singleton terms** — reduce rare terms via stopword lists

## Running the Full Benchmark Suite

```bash
cd whoosh-ng

# Run all P5 benchmarks
uv run python -m pytest tests/test_regex_tokenizer_unicode.py tests/test_token_slots.py tests/test_stemmer_compatibility.py -v

# Run full test suite
uv run python -m pytest -q
```
