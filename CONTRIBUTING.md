# Contributing to Whoosh-NG

Thank you for your interest in contributing! This document describes the
development workflow, coding standards, and quality gates for this project.

## Prerequisites

- Python 3.11 or newer
- [Git](https://git-scm.com/)
- [Ruff](https://docs.astral.sh/ruff/) for linting/formatting
- [Mypy](https://mypy.readthedocs.io/) for static type checking
- [Pyright](https://microsoft.github.io/pyright/) for additional type checking

## Setup

```bash
# Clone the repository
git clone https://github.com/<org>/whoosh-NG.git
cd whoosh-NG

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install the package in editable mode with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Branching Model

- `dev` is the main development branch.
- Create feature branches from `dev` with a descriptive name:
  `feat/search-models` or `fix/query-parser-crash`.
- Open pull requests against `dev`.
- Use **conventional commits** for all messages:
  `feat(scope):`, `fix(scope):`, `refactor(scope):`, `docs(scope):`, etc.

## Quality Gates

All contributions must pass the following checks:

```bash
# Lint
ruff check .

# Format
ruff format .

# Type checking (new code must pass without errors)
mypy src/
pyright src/

# Tests
pytest --cov=whoosh
```

### Type Checking Policy

- **New code and new modules** must pass `mypy` and `pyright` without errors.
- **Legacy code** (`src/whoosh/` core package) has known type issues and is subject to error thresholds in CI (`legacy-typecheck.yml`). Do not introduce new type errors in legacy modules without fixing existing ones in the same area.

Coverage for new modules must be >= 90%.

## Coding Standards

- Python 3.11+ type annotations on all public functions and methods.
- Google-style docstrings for all public classes and functions.
- The core `src/whoosh/` package must not depend on optional packages.
  All optional features live in subpackages (`whoosh_modern.*`, `whoosh_fastapi`,
  `whoosh_admin`, etc.).
- Follow existing code patterns and naming conventions.
- Keep commits atomic and write clear commit messages.

## Documentation

- Documentation is written in both English and French.
- Update relevant docs when changing behavior.
- Add docstrings to any new public API.

## Reporting Issues

Please use [GitHub Issues](https://github.com/<org>/whoosh-NG/issues) to report
bugs or request features. Include:

- A clear description of the issue or request.
- Steps to reproduce (for bugs).
- Expected vs actual behavior.
- Environment details (Python version, OS, etc.).

## License

By contributing, you agree that your contributions will be licensed under the
BSD 3-Clause License (see `LICENSE`).
