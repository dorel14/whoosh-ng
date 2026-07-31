# Whoosh-NG Benchmarks

This directory contains benchmarks for Whoosh-NG covering indexing, searching, and component-level performance.

## Quick Start

### 1. Build the benchmark database (required once)

```powershell
.venv\Scripts\python.exe benchmark\build_benchmark_db.py
```

This creates `benchmark/benchmark_data.db` from the included data files (Reuters articles, dictionary entries, customers, stock etablissements).

### 2. Run all benchmarks

```powershell
# End-to-end indexing + search benchmarks (CLI)
.venv\Scripts\python.exe -m benchmark --spec reuters --index --search --report csv

# Component benchmarks (pytest-benchmark) with CSV report
.venv\Scripts\python.exe -m benchmark --spec benchmark_sqlsource --report csv

# Run ALL benchmarks sequentially with reports
.venv\Scripts\python.exe -m benchmark --all --report csv --report-path all_benchmarks
```

## Available Specs

### End-to-End Specs (CLI runner)

These specs test the full indexing and search pipeline with real data. Run with `--index`, `--search`, and/or `--ranking`.

| Spec | Data | Description |
|------|------|-------------|
| `reuters` | Reuters news articles (old Whoosh API) | Index and search 21578 news articles using direct Whoosh calls |
| `reuters_modern` | Reuters news articles (new Whoosh-NG API) | Index and search 21578 news articles using SQLSource + SearchView |
| `dictionary` | dcvgr10.txt | Index and search dictionary entries |
| `customers` | customers-2000000.csv | Index and search 2M customer records |
| `stock_etab` | StockEtablissement_utf8.csv | Index and search French establishment data |

**Examples:**

```powershell
# Index only (old API)
.venv\Scripts\python.exe -m benchmark --spec reuters --index --upto 1000

# Index + search (old API)
.venv\Scripts\python.exe -m benchmark --spec reuters --index --search

# Index + search + report to JSON (old API)
.venv\Scripts\python.exe -m benchmark --spec dictionary --index --search --report json

# Limit to 500 docs, report to CSV (old API)
.venv\Scripts\python.exe -m benchmark --spec customers --index --search --upto 500 --report csv --report-path my_report

# New Whoosh-NG API (same comparison)
.venv\Scripts\python.exe -m benchmark --spec reuters_modern --index --search --report csv
```

### Component Specs (pytest-benchmark runner)

These specs test individual component performance. They follow a logical pipeline order: **data source → schema discovery → facets**.

| Step | Spec | Description |
|------|------|-------------|
| **1. Data Source** | `benchmark_sqlsource` | SQLSource data source: indexing, iteration, document count, metadata |
| **1. Data Source** | `benchmark_restsource` | RESTSource with mock server: pagination, schema discovery, indexing, search |
| **2. Schema Discovery** | `benchmark_schema_discovery` | Schema discovery from SQL columns and document samples |
| **3. Facets** | `benchmark_facets` | FacetManager performance (auto-discovery, get_facets, stats) |
| **Pipeline** | `benchmark_search_view` | SearchView pipeline: data → schema → index → facets |
| **Infrastructure** | `benchmark_middleware` | MiddlewarePipeline execution, retry, logging |
| **Infrastructure** | `benchmark_validation` | ValidationFramework (structural, search, performance, runtime) |

**Example:**

```powershell
.venv\Scripts\python.exe -m benchmark --spec benchmark_sqlsource
```

## Benchmark Pipeline

Benchmarks follow a logical data pipeline:

```
Data Source → Schema Discovery → Index Build → Facets
```

1. **Data Source** — loads and iterates documents (SQLSource, RESTSource)
2. **Schema Discovery** — discovers field types and structure from documents
3. **Index Build** — creates a Whoosh index from the schema and documents
4. **Facets** — creates facet configurations from the discovered schema

The `benchmark_search_view` spec demonstrates this full pipeline.

## Writing a New Benchmark Spec

### End-to-End Spec (CLI)

Create a new file `benchmark/my_spec.py` that subclasses `WhooshLikeSpec`:

```python
from benchmark import WhooshLikeSpec
from whoosh import fields


class MySpec(WhooshLikeSpec):
    name = "my_spec"
    main_field = "body"
    headline_field = "title"
    default_query = "test"

    def whoosh_schema(self):
        return fields.Schema(
            id=fields.ID(stored=True),
            title=fields.TEXT(stored=True),
            body=fields.TEXT(),
        )

    def documents(self):
        # Yield document dicts to index
        yield {"id": "1", "title": "Hello", "body": "Hello world"}
```

The spec is automatically discovered by `python -m benchmark --help`.

### Component Spec (pytest-benchmark)

Create a new file `benchmark/benchmark_mycomponent.py` using pytest-benchmark fixtures:

```python
import pytest

pytest.importorskip("pytest_benchmark")

from whoosh_modern.some_module import SomeComponent


class BenchmarkMyComponent:
    def setup_method(self):
        self.component = SomeComponent()

    def benchmark_something(self, benchmark):
        def _run():
            return self.component.do_something()

        result = benchmark(_run)
        assert result is not None
```

Run with: `python -m benchmark --spec benchmark_mycomponent`

## Understanding Benchmark Results

Component benchmarks (pytest-benchmark) produce a results table like this:

```
Name (time in ns)    Min              Max              Mean           StdDev    Median     IQR    Outliers     OPS        Rounds  Iterations
```

| Column | Meaning |
|--------|---------|
| **Name** | Benchmark function name |
| **Min** | Fastest single execution (ns) |
| **Max** | Slowest single execution (ns) |
| **Mean** | Average execution time (ns) |
| **StdDev** | Standard deviation of execution times (ns) |
| **Median** | Median execution time (ns) |
| **IQR** | Interquartile range (Q3 - Q1) (ns) |
| **Outliers** | Count of outliers: `1 SD from Mean; 1.5 IQR from Q1/Q3` |
| **OPS** | Operations per second (`1 / Mean`). `0.00` means too slow to compute meaningfully |
| **Rounds** | Number of benchmark rounds performed |
| **Iterations** | Number of iterations per round |

### Relative comparison

Numbers in parentheses after each value show the ratio compared to the **fastest benchmark** (which is always `1.0`):

- `1.0` = fastest benchmark in this run
- `230.27` = 230× slower than the fastest
- `>1000.0` = more than 1000× slower than the fastest (display cap)

### Color coding

- **Green** (`.`) = test passed
- **Red** (`F`) = test failed (error or assertion failure)

### Interpreting OPS

- High OPS = fast operation (more operations per second)
- `OPS: 0.00` = the operation is so slow it can't complete enough iterations to compute a meaningful rate

| Option | Default | Description |
|--------|---------|-------------|
| `--spec` | *(required unless `--all`)* | Benchmark spec name |
| `--all` | - | Run all benchmarks sequentially |
| `--index` | - | Run indexing benchmark (end-to-end specs only) |
| `--search` | - | Run querying benchmark (end-to-end specs only) |
| `--ranking` | - | Run ranking benchmark (end-to-end specs only) |
| `--dir` | benchmark dir | Working directory for index/data |
| `--report` | none | Report format: csv, json, none (works for all specs) |
| `--report-path` | benchmark_report | Report file path (without extension) |
| `--limit` | 10 | Max search results |
| `--procs` | 0 | Number of processors for indexing |
| `--limitmb` | 128 | Max memory per writer (MB) |
| `--skip` | 1 | Initial docs to skip |
| `--upto` | 0 | Max docs to index (0=unlimited) |
| `--merge` | 1 | Merge policy (1=SMALL, 0=none) |
| `--pytest-args` | "" | Extra args for pytest (component specs only) |

### Report Metrics

End-to-end specs produce the following metrics in CSV/JSON reports:

| Metric | Category | Unit | Description |
|--------|----------|------|-------------|
| `indexed_docs` | indexing | docs | Number of documents indexed |
| `docs_per_sec` | indexing | docs/s | Indexing throughput |
| `search_time` | querying | s | Search elapsed time |
| `search_results` | querying | results | Number of search results returned |