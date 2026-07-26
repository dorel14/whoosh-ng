---
color_scheme: dark
title: "Installation"
nav_order: 20
parent: "Getting Started"
---

# Installation

## Requirements

- Python 3.10+
- No mandatory dependencies (pure Python)
- Optional extras for advanced features

## pip install

```bash
pip install whoosh-ng
```

## Extras

| Extra | Description |
|-------|-------------|
| `vector` | NumPy-based vector providers |
| `autocomplete` | Autocomplete plugin |
| `api` | FastAPI plugin |
| `metrics` | Prometheus metrics integration |
| `all` | Install everything |

```bash
pip install whoosh-ng[all]
```

## Development install

```bash
git clone https://github.com/your-org/whoosh-NG.git
cd whoosh-NG
uv sync --extra dev
```

## Verification

```bash
uv run pytest tests/ -q
uv run ruff check src/ tests/
uv run ruff format --check .
uv run mypy src/whoosh
```

## Next Steps

- [Quick Start](/en/quickstart)
- [Core Concepts](/en/guides/core-concepts)
