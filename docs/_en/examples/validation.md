---
title: "Validation Framework"
nav_order: 243
---

# Validation Framework

The validation framework runs checks against a data source before indexing. It provides 4 distinct validation levels with different failure modes.

## Validation Levels

| Level | Method | Purpose |
|-------|--------|---------|
| **Level 1** | `validate_structural(source)` | DataSource availability, schema detection |
| **Level 2** | `validate_search(schema)` | Indexable fields, analyzer compatibility |
| **Level 3** | `validate_performance(schema, source)` | Performance warnings (TEXT fields, etc.) |
| **Level 4** | `validate_runtime(source, sample_size)` | Sample iteration, type validation |

## Basic Usage

```python
from whoosh_modern.validation import ValidationFramework, ValidationResult
from whoosh_modern.data_sources.sql import SQLSource
import sqlite3

conn = sqlite3.connect("benchmark/benchmark_data.db")
source = SQLSource(connection=conn, query="SELECT * FROM reuters_articles")

validator = ValidationFramework()

# Run all 4 validation levels
results: list[ValidationResult] = validator.validate(source)

for result in results:
    level_name = f"Level {result.level}"
    status = "PASS" if result.passed else "FAIL"
    print(f"{level_name}: {status}")
    for error in result.errors:
        print(f"  ERROR: {error}")
    for warning in result.warnings:
        print(f"  WARN: {warning}")
```

## Individual Level Validation

```python
# Level 1: Structural
errors = validator.validate_structural(source)

# Level 2: Search
from whoosh.fields import Schema
schema = source.discover_schema()
errors = validator.validate_search(schema)

# Level 3: Performance
warnings = validator.validate_performance(schema, source)

# Level 4: Runtime
errors = validator.validate_runtime(source, sample_size=100)
```

## Validation Results

```python
@dataclass
class ValidationResult:
    level: int
    passed: bool
    warnings: list[str]
    errors: list[str]
```
