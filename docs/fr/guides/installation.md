---
color_scheme: dark
title: "Installation"
nav_order: 20
parent: "Prise en main"
lang: fr
---

# Installation

## Prérequis

- Python 3.10+
- Aucune dépendance obligatoire (pur Python)
- Extras optionnels pour les fonctionnalités avancées

## pip install

```bash
pip install whoosh-ng
```

## Extras

| Extra | Description |
|-------|-------------|
| `vector` | Providers de recherche vectorielle (NumPy, HNSW, Faiss) |
| `autocomplete` | Plugin d'autocomplétion |
| `api` | Plugin FastAPI |
| `metrics` | Intégration Prometheus |
| `all` | Installer tout |

```bash
pip install whoosh-ng[all]
```

## Installation pour le développement

```bash
git clone https://github.com/your-org/whoosh-NG.git
cd whoosh-NG
uv sync --extra dev
```

## Vérification

```bash
uv run pytest tests/ -q
uv run ruff check src/ tests/
uv run ruff format --check .
uv run mypy src/whoosh
```

## Prochaines étapes

- [Démarrage rapide](/fr/quickstart)
- [Concepts fondamentaux](/fr/guides/core-concepts)
