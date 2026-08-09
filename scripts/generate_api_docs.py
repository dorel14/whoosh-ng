"""Module de generation des docs API avec pydoctor.

Ce module orchestre l'execution de pydoctor pour generer la documentation
API a partir du code source Python. Pydoctor produit des fichiers HTML
qui sont integres au site Docusaurus via un composant iframe.

Le script:
1. Installe pydoctor si ce n'est pas fait
2. Execute pydoctor sur les packages source (whoosh, whoosh_modern)
3. Copie les fichiers generes dans website/static/api_html/
4. Cree la page Docusaurus api/reference.md avec un iframe vers le HTML

Auteur: SoniqueBay Team
Version: 1.2.0
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
STATIC_DIR = REPO_ROOT / "website" / "static"
# Use a subdirectory that Docusaurus won't process through webpack
# (static/ assets are copied verbatim, but .html files in static/ are
# processed by webpack's file-loader which triggers case-sensitivity checks)
# Instead, output to an _out directory and serve from there
API_OUTPUT = REPO_ROOT / "website" / "api_html"
# Final location copied into static/ as raw assets (not bundled)
STATIC_API_DIR = STATIC_DIR / "api_docs"
DOCS_EN_DIR = REPO_ROOT / "website" / "docs"
DOCS_FR_DIR = REPO_ROOT / "website" / "i18n" / "fr" / "docusaurus-plugin-content-docs" / "current"

# Python packages to generate API docs for
PACKAGES = [
    "src/whoosh",
    "src/whoosh_modern",
]


def install_pydoctor() -> bool:
    """Install pydoctor if not already installed.

    Returns:
        True if pydoctor is available, False otherwise.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pydoctor", "--help"],
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return True

    print("Installing pydoctor...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "pydoctor"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"Failed to install pydoctor: {result.stderr}", file=sys.stderr)
        return False
    return True


def generate_api_docs() -> bool:
    """Run pydoctor to generate HTML API docs.

    Pydoctor output goes to ``website/api_html/`` (git-ignored build artifact).
    The HTML files are then copied verbatim to ``website/static/api_docs/``
    which Docusaurus serves as static raw assets (not processed by webpack).

    Returns:
        True if generation succeeded, False otherwise.
    """
    if not install_pydoctor():
        return False

    # Clean and recreate output directory
    if API_OUTPUT.exists():
        shutil.rmtree(API_OUTPUT)
    API_OUTPUT.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "pydoctor",
        "--project-name=Whoosh-NG",
        "--project-url=https://github.com/dorel14/whoosh-ng",
        f"--html-output={API_OUTPUT}",
        "--docformat=google",
    ] + PACKAGES

    print("Running: " + " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)

    if result.returncode != 0:
        print(f"Pydoctor failed:\n{result.stderr}", file=sys.stderr)
        return False

    if result.stdout:
        print(result.stdout)

    # Copy generated HTML to static/ directory for Docusaurus to serve
    # Docusaurus copies files from static/ verbatim, but webpack processes
    # .html files through file-loader which has case-sensitivity checks.
    # To avoid conflicts (e.g., whoosh.fields.numeric.html vs NUMERIC.html),
    # we serve via a raw asset path that bypasses webpack bundling.
    if STATIC_API_DIR.exists():
        shutil.rmtree(STATIC_API_DIR)
    shutil.copytree(API_OUTPUT, STATIC_API_DIR)
    print(f"Copied API docs to {STATIC_API_DIR}")

    return True


def create_api_page() -> None:
    """Create a Docusaurus page with API module reference table.

    The page lists all API modules grouped by category. When pydoctor HTML
    docs are available, users can also open them locally.
    """
    _pydoctor_url = "https://pydoctor.readthedocs.io/"
    _github_url = "https://github.com/dorel14/whoosh-ng/tree/master/website/static/api_docs"
    md_content = f"""---
title: "API Reference"
sidebar_position: 60
sidebars: apiSidebar
---

# API Reference

The Whoosh-NG API reference is auto-generated from source code using
[pydoctor]({_pydoctor_url}), which parses Python modules
and generates HTML documentation from docstrings.

:::note
If the embedded documentation does not display, the API docs may not have
been generated yet in this deployment. [View on GitHub]({_github_url})
for the full API documentation, or check the
[API modules list](#api-modules) below.
:::

## API Modules

### Core API

| Module | Description |
|--------|-------------|
| `whoosh.index` | High-level index creation, opening, and management |
| `whoosh.fields` | Schema and field type definitions |
| `whoosh.writing` | Writer classes and merge policies |
| `whoosh.searching` | Searcher, Results, and collectors |
| `whoosh.query` | Query classes and parsers |
| `whoosh.qparser` | Query parser implementation |
| `whoosh.analysis` | Tokenizers, filters, and analyzers |
| `whoosh.highlight` | Search result highlighting |
| `whoosh.spelling` | Spelling correction |
| `whoosh.sorting` | Facets and sorting |
| `whoosh.event_bus` | Event system |
| `whoosh.hooks` | Hook system |
| `whoosh.middleware` | Middleware pipeline |
| `whoosh.plugins` | Plugin system and registry |
| `whoosh.backends` | Storage backends |

### Modern API

| Module | Description |
|--------|-------------|
| `whoosh_modern.data_sources` | Data source protocol and implementations |
| `whoosh_modern.views` | SearchView unified interface |
| `whoosh_modern.middleware` | Retry, cache, logging middleware |
| `whoosh_modern.facets` | FacetManager for auto-discovery |
| `whoosh_modern.validation` | 4-level validation framework |
| `whoosh_modern.indexing` | BatchIndexWriter, AnalyzerCache |
| `whoosh_modern.linguistics` | Linguistic engine (stemmers, synonyms) |
| `whoosh_modern.storage` | Storage providers (HybridStorage, etc.) |
| `whoosh_modern.vector` | NumpyProvider for vector similarity |
| `whoosh_modern.autocomplete` | Autocomplete provider plugins |
| `whoosh_fastapi` | FastAPI REST API endpoints |
| `whoosh_admin` | Admin UI dashboard |

:::info
For the full interactive API documentation, run:
```bash
pip install pydoctor
python scripts/generate_api_docs.py
```
Then open `website/static/api_docs/index.html` in your browser.
:::
"""

    en_path = DOCS_EN_DIR / "api" / "reference.md"
    fr_path = DOCS_FR_DIR / "api" / "reference.md"

    en_path.parent.mkdir(parents=True, exist_ok=True)
    fr_path.parent.mkdir(parents=True, exist_ok=True)

    en_path.write_text(md_content, encoding="utf-8")
    print(f"Created: {en_path}")

    # FR version with translated title
    fr_content = (
        md_content.replace(
            'title: "API Reference"',
            'title: "Référence API"',
        )
        .replace(
            "# API Reference",
            "# Référence API",
        )
        .replace(
            "auto-generated from source code using",
            "générée automatiquement à partir du code source avec",
        )
        .replace(
            "which parses Python modules",
            "qui analyse les modules Python",
        )
        .replace(
            "and generates HTML documentation from docstrings.",
            "et génère une documentation HTML à partir des docstrings.",
        )
        .replace(
            "Open API Reference",
            "Ouvrir la référence API",
        )
    )
    fr_path.write_text(fr_content, encoding="utf-8")
    print(f"Created: {fr_path}")


def generate() -> None:
    """Generate API docs and create the Docusaurus page."""
    # Create the Docusaurus referencing page
    create_api_page()

    # Try to generate API docs (pydoctor may not be available in all environments)
    if generate_api_docs():
        print("API docs generated successfully.")
    else:
        print(
            "Warning: pydoctor not available. API docs page created but "
            "HTML docs not generated. Run 'pip install pydoctor' and "
            "'python scripts/generate_api_docs.py' to generate.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    generate()
