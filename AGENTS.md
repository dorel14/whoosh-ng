# AGENTS.md — Instructions for AI Agents

> **Repository**: [whoosh-ng](https://github.com/dorel14/whoosh-ng)
> **Current branch**: `master` (development: `dev`)
> **Python**: 3.11+ required
> **Last updated**: 2026-08-08

---

## 1. Project Overview

**Whoosh-NG** is a modern, pure-Python full-text indexing and search library. It is a fork and evolution of the original `whoosh` library, bringing Python 3.11+ support, strict type annotations, optional feature profiles (vector search, async, FastAPI, metrics), a plugin architecture, a middleware pipeline, and an event/hook system.

The library provides:
- **BM25/BM25F** scoring with phrase queries
- **Fielded documents** with typed fields
- **Query parsing** with boosting and syntax options
- **Facets & sorting**, **highlighting**, **spell checking**
- **Plugin system** with entry-point auto-discovery
- **Middleware pipeline** for cross-cutting concerns (metrics, caching, compression, encryption)
- **Event bus** and **hook system**
- Optional extensions: vector search, async, FastAPI REST API, Prometheus metrics, FastAPI Admin UI

**Version management**: Semantic versioning is enforced automatically via `python-semantic-release` (conventional commit parser) on `master` merges. Version bumps happen in `pyproject.toml` and `src/whoosh/__init__.py` (see `scripts/sync_version.py`).

---

## 2. Repository Structure

```
whoosh-ng/
├── src/                        # Source code (Python packages)
│   ├── whoosh/                 # Core engine (legacy-compatible namespace)
│   │   ├── analysis/           # Tokenizers, filters, analyzers
│   │   ├── automata/           # FSA / FST
│   │   ├── backends/           # Storage backends (File, SQLite)
│   │   ├── codec/              # Posting format codecs
│   │   ├── collectors/         # Result collectors
│   │   ├── columns/            # Column storage
│   │   ├── fields/             # Schema and field types
│   │   ├── filedb/             # File-based storage (legacy)
│   │   ├── highlight/          # Highlighting
│   │   ├── lang/               # Stemmers, stopwords, languages
│   │   ├── matching/           # Matchers
│   │   ├── middleware/         # Middleware base, chain, wrappers
│   │   ├── plugins/            # PluginManager, Plugin base, registries
│   │   ├── providers/          # Vector providers (HNSW, etc.)
│   │   ├── qparser/            # Query parser
│   │   ├── query/              # Query classes
│   │   ├── reading/            # Index readers
│   │   ├── registry/           # Generic + typed registries
│   │   ├── searching/          # Searcher, Results
│   │   ├── sorting/            # Facets, sorting
│   │   ├── support/            # Utilities, charset, etc.
│   │   ├── util/               # Utilities (compat, times, etc.)
│   │   ├── utils/              # Async utils
│   │   ├── vector/             # Vector search base
│   │   ├── writing/            # Index writers
│   │   ├── event_bus.py        # Event bus
│   │   ├── hooks.py            # Hook system
│   │   ├── index.py            # Index creation/opening
│   │   ├── scoring.py          # Scoring algorithms
│   │   ├── spelling.py         # Spell checking
│   │   └── ...
│   ├── whoosh_modern/          # Modern extensions (data sources, views, etc.)
│   │   ├── analysis/           # Stemmer providers
│   │   ├── autocomplete/       # Autocomplete providers
│   │   ├── data_sources/       # DataSource protocol + implementations
│   │   ├── facets/             # FacetManager
│   │   ├── indexing/           # BatchIndexWriter, AnalyzerCache
│   │   ├── linguistics/        # Linguistic engine (stemmers, synonyms)
│   │   ├── middleware/         # Retry, Cache, Logging middleware
│   │   ├── models/             # Pydantic, SQLAlchemy, SQLModel integrations
│   │   ├── profiling/          # Benchmarking utilities
│   │   ├── storage/            # Storage providers
│   │   ├── vector/             # NumpyProvider
│   │   ├── views/              # SearchView
│   │   ├── writer/             # Modern writers
│   │   ├── application.py      # SearchApplication
│   │   └── ...
│   ├── whoosh_fastapi/         # FastAPI REST API integration
│   └── whoosh_admin/           # Admin UI plugin
├── tests/                      # Test suite (pytest)
├── benchmark/                  # Benchmarking scripts
├── stress/                     # Stress tests
├── scripts/                    # Utility scripts (sync_version, checkpoints, etc.)
├── website/                    # Docusaurus documentation site
│   ├── docs/                   # Documentation source (.md)
│   │   ├── api/                # API reference
│   │   ├── core/               # Core concepts (EN source)
│   │   ├── examples/           # Runnable code examples
│   │   ├── modern/             # Modern feature docs
│   │   ├── index.md            # Root page
│   │   ├── llms.txt            # LLM-friendly index
│   │   ├── llms-full.txt       # LLM-friendly full docs
│   │   └── _fr/                # French translations (i18n)
│   ├── i18n/                   # Docusaurus i18n translations
│   └── docusaurus.config.ts    # Docusaurus configuration
├── docs/                       # Legacy docs (archived; see §6)
│   ├── archive/                # Old Sphinx docs
│   ├── archive_jekyll/         # Old Jekyll site (_en, _fr) — archived
│   └── llms.txt / llms-full.txt  # Symlinks/copies for GitHub Pages
├── .github/                    # GitHub workflows, issue templates
├── .kilo/                      # Kilo AI agent configuration and plans
├── pyproject.toml              # Project metadata, dependencies, tool config
├── CHANGELOG.md                # English changelog (Keep a Changelog)
├── CHANGELOG.fr.md             # French changelog (auto-translated)
├── README.md                   # Project README
├── CONTRIBUTING.md             # Contributor guide
├── AGENTS.md                   # ← This file
└── LICENSE.txt                 # BSD-2-Clause
```

**Key packages**:
| Package | Description |
|---|---|
| `whoosh` | Core engine (import namespace remains `whoosh`) |
| `whoosh_modern` | Modern extensions: data sources, views, models, middleware, profiling, linguistics |
| `whoosh_fastapi` | FastAPI REST endpoints (search, autocomplete, vector, health) |
| `whoosh_admin` | Admin UI dashboard |

---

## 3. Development Setup

### Prerequisites
- Python 3.11 or newer (3.12 recommended)
- [Git](https://git-scm.com/)
- [Ruff](https://docs.astral.sh/ruff/) for linting/formatting
- [Mypy](https://mypy.readthedocs.io/) and [Pyright](https://microsoft.github.io/pyright/) for type checking

### Environment

```bash
# Clone the repository
git clone https://github.com/dorel14/whoosh-ng.git
cd whoosh-ng

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install in editable mode with dev + common optional extras
pip install -e ".[dev,models,api,vector]"

# Alternative: use uv (recommended for speed)
uv sync && uv run --env
```

### Install pre-commit hooks
```bash
pre-commit install
```

### Quick verification
```bash
ruff check .          # lint
ruff format .         # format
mypy src/             # type checking
pyright src/          # additional type checking
pytest                # run tests
```

---

## 4. Code Conventions

### 4.1 Module Docstrings

Every Python module must start with a structured module-level docstring. The docstring should describe what the module does, its purpose, and include metadata. All modules follow this template:

```python
"""<Concise description of the module's purpose.>

<One or more paragraphs describing what the module provides,
its key classes/functions, and how it fits into the larger architecture.
Be specific and avoid generic boilerplate.>

Auteur: SoniqueBay Team
Version: <SemVer version>
"""
```

**Example**:
```python
"""Module de chargement et parsing de la taxonomie des genres depuis YAML.

Ce module fournit des fonctions pour charger la hiérarchie des genres depuis
genre-tree.yaml et générer les mappings nécessaires pour la normalisation
et la compatibilité des genres.

Auteur: SoniqueBay Team
Version: 1.0.0
"""
```

The `Version` should be incremented when the module's public API changes or when significant refactoring occurs.

### 4.2 Type Annotations

- Python 3.11+ type annotations on **all** public functions, methods, and module-level variables.
- Use `from __future__ import annotations` at the top of every module (before any other imports except `__future__` and comments/docstrings).
- **New code** must pass both `mypy --strict` and `pyright` without errors.
- **Legacy code** (`src/whoosh/` core package) has known type issues and is excluded from strict checks in CI (`legacy-typecheck.yml`). Do not introduce new type errors in legacy modules; if you must, fix existing ones in the same area.

### 4.3 Docstrings (Functions & Classes)

- Use **Google-style** docstrings for all public classes and functions.
- Include `Args:`, `Returns:`, `Raises:`, and `Example:` sections where applicable.

```python
def search(query: str, limit: int = 10) -> SearchResults:
    """Execute a search query and return matching documents.

    Args:
        query: The search query string.
        limit: Maximum number of results to return.

    Returns:
        SearchResults containing hits, facets, and metadata.

    Raises:
        SearchError: If the query is malformed or the index is unavailable.

    Example:
        >>> results = index.search("python search")
        >>> for hit in results:
        ...     print(hit["title"])
    """
```

### 4.4 Comments

- Comments should explain **why**, not **what**.
- Use section comments to break up large functions.
- For non-obvious algorithms, add inline comments.
- Comment `# type: ignore[...]` is used in legacy modules to suppress mypy errors — do not remove without replacing with proper typing.

### 4.5 Import Ordering

- Imports are organized by `ruff` with `isort` rules:
  1. Standard library imports
  2. Third-party imports
  3. First-party imports (`whoosh`, `whoosh_modern`, `whoosh_fastapi`, `whoosh_admin`)
- Use absolute imports, not relative.

### 4.6 Naming Conventions

- `snake_case` for functions, variables, methods
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Private members prefixed with `_`
- Avoid: `N802`, `N803`, etc. violations (see per-file ignores in `pyproject.toml`)

### 4.7 Core Package Boundaries

- The core `src/whoosh/` package **must not depend** on optional packages (numpy, fastapi, boto3, etc.).
- All optional features live in subpackages: `whoosh_modern.*`, `whoosh_fastapi`, `whoosh_admin`, etc.

---

## 5. Testing Conventions

### Test Structure
- Tests live in `tests/` and follow the pattern `test_*.py`.
- Test modules mirror the source structure (e.g., `tests/test_data_sources/`).
- Async tests are marked with `@pytest.mark.asyncio`.

### Running Tests

```bash
# Full test suite with coverage
pytest

# Specific module
pytest tests/test_query_parser.py

# Verbose
pytest -v

# Benchmark-only (requires pytest-benchmark)
pytest tests/ --benchmark-only
```

### Coverage Requirements
- **New modules**: >= 90% coverage
- **Release**: >= 95% coverage
- Coverage is enforced via `--cov=whoosh --cov=whoosh_modern --cov=whoosh_fastapi --cov=whoosh_admin`
- Reports: terminal, HTML (`htmlcov/`), XML (`coverage.xml`)

### Quality Gates (non-negotiable)
Every contribution must pass:
```bash
ruff check .          # 0 errors
mypy src/             # 0 errors (new code); legacy has thresholds
pyright src/          # 0 errors (new code)
pytest                # 100% green
```

### Test Markers
```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slower integration-style checks",
    "asyncio: marks tests as async",
]
```

---

## 6. Documentation Conventions

### 6.1 Documentation Philosophy

Documentation is delivered **continuously** with each Epic/Sprint. **Separate documentation sprints are prohibited.** Every feature must ship with its documentation in the same development cycle.

The documentation is written in **Markdown (`.md`)** and uses [Docusaurus 3](https://docusaurus.io/) for site generation. The site is published to GitHub Pages from `master` branch `/docs` folder (see `.github/workflows/pages.yml`).

### 6.2 Documentation Structure

```
website/docs/
├── index.md              # Root documentation page
├── llms.txt              # LLM-friendly index (sitemap of links)
├── llms-full.txt         # LLM-friendly full API docs (concatenated)
├── api/                  # API reference (auto-generated or hand-written)
├── core/                 # Core Whoosh concepts (EN source language)
├── modern/               # Modern Whoosh-NG features
├── examples/             # Runnable code examples
└── _fr/                  # French translations (mirrored structure)
```

### 6.3 Content Rules

1. **Two languages**: English (source) and French (translation). Both must stay synchronized.
2. **Code examples** are in English for consistency, even in French docs.
3. **Frontmatter**: Every doc page must have YAML frontmatter with `title` and `sidebar_position`.
4. **Version tracking**: Documentation pages that describe specific modules should include a `Version:` line (e.g., `Version: 2.0.0`).
5. **Module references**: Use `Module:` to indicate which source module a doc page covers.

### 6.4 Documentation Checklist (Definition of Done for docs)

Every new Epic/Sprint must deliver:
- [ ] **User Guide** — `docs/core/` or `docs/modern/`
- [ ] **Developer Guide** — architecture notes, implementation details
- [ ] **API Reference** — `docs/api/`
- [ ] **Migration Guide** — if breaking changes are introduced
- [ ] **Examples** — minimal, intermediate, advanced runnable examples
- [ ] **Changelog entry** — in `CHANGELOG.md` (English) and `CHANGELOG.fr.md` (French)

### 6.5 Archiving Policy

Documents that are **not intended for publication** (obsolete specs, experimental notes, meeting notes, internal planning) must be **archived** in a designated directory. The project uses:

- `.kilo/plans/` — Planning documents, specs, roadmaps (not published to docs site)
- `docs/archive/` — Old Sphinx documentation (legacy, not maintained)
- `docs/archive_jekyll/` — Old Jekyll site content (`_en/`, `_fr/`) — archived after migration to Docusaurus

**Rule**: Any document in `docs/` root or `docs/archive*` that is no longer the active documentation source should be moved to the appropriate archive subdirectory. The `.jekyll-cache/` directory should never be committed.

### 6.6 LLM-Friendly Docs

- `llms.txt` and `llms-full.txt` (both at root and in `website/docs/`) must be kept up to date.
- `llms.txt` is an index of all documentation pages with links.
- `llms-full.txt` contains the complete API documentation concatenated.
- These files are excluded from `.gitignore` patterns (`!llms.txt`, `!llms-full.txt`).

---

## 7. Git Workflow

### Branching Model
- `master` — stable release branch (tagged releases, semantic versioning)
- `dev` — main development branch (active work happens here)
- Feature branches — created from `dev` with descriptive names:
  - `feat/search-models`
  - `fix/query-parser-crash`
  - `docs/update-storage-provider-guide`

### Commit Messages
Use **Conventional Commits**:
```
feat(scope): add vector search provider
fix(scope): resolve NoneType error in searcher
refactor(scope): simplify middleware registration
docs(scope): update plugin development guide
perf(scope): optimize tokenization pipeline
test(scope): add edge case tests for facets
chore(scope): update dependencies
```

Format: `<type>(<scope>): <subject>`
Types: `feat`, `fix`, `refactor`, `style`, `perf`, `test`, `docs`, `chore`, `ci`, `build`

### Pull Requests
- Open PRs against `dev`.
- PR title should follow conventional commits format.
- Include a description of changes, rationale, and breaking changes (if any).
- All CI checks must pass.
- Auto-merge is configured for Dependabot and trusted PRs (see `.github/workflows/auto-merge.yml`).

### Releases
- **Semantic versioning** via `python-semantic-release`.
- Triggered on `master` branch merges with conventional commits.
- Version is auto-bumped in `pyproject.toml` and `src/whoosh/__init__.py`.
- Changelog is auto-generated from conventional commits.

---

## 8. CI/CD Workflows

Located in `.github/workflows/`:

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | PR to `dev`, push to `dev` | Lint (ruff/mypy/pyright), test matrix (3.11/3.12/3.13), build |
| `legacy-typecheck.yml` | PR to `dev` | Permissive type checking for legacy `src/whoosh/` modules |
| `semantic-release.yml` | Push to `master` | Auto-version bump, changelog, PyPI release |
| `pages.yml` | Push to `master` | Build and deploy Docusaurus site to GitHub Pages |
| `sync-changelog.yml` | Push to `dev` (CHANGELOG.md changes) | Auto-translate changelog to French via Gemini |
| `sync-version.yml` | Push to `master` | Synchronize version strings across files |
| `llms-doc.yml` | Push to `master` | Regenerate `llms.txt` / `llms-full.txt` |
| `api-docs.yml` | Push to `master` | Generate API reference docs (pydoctor) |
| `benchmark.yml` | Scheduled (weekly) | Run performance benchmarks |
| `codeql.yml` | Push/PR | Security code analysis |
| `first-interaction.yml` | New issue/PR | Welcome and label first-time contributors |
| `issue_labeler.yml` | New issue | Auto-label based on patterns |
| `gemini-review.yml` | PR | AI code review via Gemini |
| `stale_bot.yaml` | Scheduled | Close stale issues/PRs |

---

## 9. Common Commands for Agents

### Development
```bash
pip install -e ".[dev,models,api,vector]"   # editable install with extras
pre-commit install                          # install git hooks
pre-commit run --all-files                  # run all pre-commit checks
```

### Quality Checks
```bash
ruff check .                              # lint all files
ruff check --fix .                        # lint + auto-fix
ruff format .                             # format code
mypy src/                                 # type checking (strict on new code)
pyright src/                              # additional type checking
```

### Testing
```bash
pytest                                    # full test suite with coverage
pytest -x                                 # stop on first failure
pytest tests/test_files.py -v             # specific test file
pytest --benchmark-only                   # benchmark tests only
pytest --cov-report=html                  # HTML coverage report
```

### Documentation
```bash
cd website
npm install                               # install Docusaurus deps
npm run start                             # dev server (localhost:3000)
npm run build                             # production build
```

### Semantic Release (manual, if needed)
```bash
pip install python-semantic-release
semantic-release version --major          # or --minor / --patch / --prerelease
```

---

## 10. Kilo Agent Configuration

The `.kilo/` directory contains project-specific Kilo configuration:

- `.kilo/kilo.jsonc` — Kilo configuration (indexing, snapshot settings)
- `.kilo/plans/` — Planning documents, specs, and roadmaps (not published)
- `.kilo/agent-manager.json` — Agent Manager session state (UI persistence, do not edit manually)
- `.kilo/.gitignore` — Ignores `node_modules`, `package.json`, etc.

**Note**: `.kilo` is in `.gitignore` at the repository root (line 25: `/.kilo`). Kilo-specific tooling files are managed separately.

### Kilo Plans
Specifications are organized in:
- `.kilo/plans/global_plan.md` — V1/V2/V3 roadmap overview
- `.kilo/plans/1786003980063-whoosh-ng-roadmap.md` — Consolidated roadmap
- `.kilo/plans/specs/` — Executable specs by sprint/lot
  - `lot1-sprint-c-middleware-plugins.md`
  - `lot1-sprint-d-synonyms-linguistics-stemmers.md`
  - `lot1-sprint-e-async.md`
  - `lot1-sprint-f-fastapi-admin.md`
  - etc.

---

## 11. Key Architectural Decisions

1. **Sync core, async ecosystem**: The core search engine remains synchronous. Async support is layered on top via `asyncio.to_thread()` bridges and async protocols (`AsyncDataSource`, `AsyncStorageProvider`, etc.).

2. **Plugin-first architecture**: All extensibility (vector providers, data sources, middleware, analyzers) is done through plugins discovered via Python entry points.

3. **Protocol-first**: Major abstractions use Python `Protocol` classes (e.g., `DataSource`, `Backend`, `VectorProvider`).

4. **Optional dependencies**: Features like vector search, FastAPI, and metrics are optional extras. The core package has zero mandatory third-party dependencies (only `cached-property`).

5. **Semantic versioning**: Automated via `python-semantic-release` with conventional commit parsing. Version is synchronized across `pyproject.toml`, `src/whoosh/__init__.py`, and `README.md`.

6. **Documentation policy**: Docs are delivered continuously with each sprint — never in a separate sprint. All docs are in Markdown for GitHub Wiki compatibility and Docusaurus rendering.

7. **Storage providers**: `HybridStorage` (local cache + remote S3) is the recommended pattern for production. `PostgreSQLStorage` has been removed in favor of the hybrid approach.

---

## 12. Where to Start

If you're an AI agent assigned to a task, follow this workflow:

1. **Read** `AGENTS.md` (this file) and `CONTRIBUTING.md` for project context.
2. **Survey** the relevant spec in `.kilo/plans/specs/` if the task is feature work.
3. **Locate** relevant source files using `grep` or `codebase_search`.
4. **Write code** following the conventions in §4 (module docstrings, type annotations, Google-style docstrings).
5. **Write tests** — new modules require >= 90% coverage.
6. **Run quality gates**: `ruff check`, `mypy`, `pyright`, `pytest`.
7. **Update documentation** in `website/docs/` if the change affects public API or behavior.
8. **Update** `CHANGELOG.md` with a concise entry.
9. **Use conventional commits** for the git commit message.

---

## 13. Useful File References

| File | Purpose |
|---|---|
| `pyproject.toml` | All project config: dependencies, ruff, mypy, pyright, pytest, semantic_release |
| `pyrightconfig.json` | Pyright configuration (includes/excludes for legacy modules) |
| `.pre-commit-config.yaml` | Pre-commit hooks: ruff, mypy, pyright, sync-version |
| `CONTRIBUTING.md` | Contributor workflow guide |
| `CHANGELOG.md` | English changelog |
| `CHANGELOG.fr.md` | French changelog (auto-translated) |
| `scripts/sync_version.py` | Version synchronization script |
| `website/docusaurus.config.ts` | Docusaurus site configuration |
| `README.md` | Project overview and quick start |
