---
title: "Framework de validation"
nav_order: 243
lang: fr
---

# Framework de validation

Le framework de validation exécute 4 niveaux de vérifications sur une source de données avant l'indexation.

## Les 4 niveaux

| Niveau | Méthode | Objectif |
|-------|---------|---------|
| **Niveau 1** | `validate_structural(source)` | Disponibilité de la source, détection de schéma |
| **Niveau 2** | `validate_search(schema)` | Champs indexables, compatibilité des analyseurs |
| **Niveau 3** | `validate_performance(schema, source)` | Avertissements de performance (TEXT, etc.) |
| **Niveau 4** | `validate_runtime(source, sample_size)` | Itération d'échantillon, validation de types |

## Usage basique

```python
from whoosh_modern.validation import ValidationFramework, ValidationResult
from whoosh_modern.data_sources.sql import SQLSource
import sqlite3

conn = sqlite3.connect("benchmark/benchmark_data.db")
source = SQLSource(connection=conn, query="SELECT * FROM reuters_articles")

validator = ValidationFramework()
results: list[ValidationResult] = validator.validate(source)

for result in results:
    status = "PASS" if result.passed else "FAIL"
    print(f"Niveau {result.level}: {status}")
```

## Validation individuelle

```python
errors = validator.validate_structural(source)
errors = validator.validate_search(schema)
warnings = validator.validate_performance(schema, source)
errors = validator.validate_runtime(source, sample_size=100)
```