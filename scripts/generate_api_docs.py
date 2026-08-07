"""Module de generation des docs API avec pydoctor.

Ce module orchestre l'execution de pydoctor pour generer la documentation
API a partir du code source Python. Pydoctor produit des fichiers HTML
qui sont integres au site Docusaurus via un composant iframe ou un lien.

Le script:
1. Installe pydoctor si ce n'est pas fait
2. Execute pydoctor sur les packages source (whoosh, whoosh_modern)
3. Copie les fichiers generes dans website/static/api/
4. Met a jour le menu de navigation pour inclure le lien vers les API docs

Auteur: SoniqueBay Team
Version: 1.1.0
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
STATIC_DIR = REPO_ROOT / "website" / "static"
API_OUTPUT = STATIC_DIR / "api"
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
        sys.executable, "-m", "pydoctor",
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
    return True


def create_api_page() -> None:
    """Create a Docusaurus page that embeds the pydoctor HTML output.

    The page uses an iframe to display the pydoctor HTML docs.
    """
    md_content = '''---
title: "API Reference"
sidebar_position: 60
---

# API Reference

The Whoosh-NG API reference is auto-generated from source code using
[pydoctor](https://pydoctor.readthedocs.io/), which parses Python modules
and generates HTML documentation from docstrings.

:::note
If the embedded documentation does not display, you can also view the
full API docs in a new tab:
[Open API Reference](/api/index.html)
:::

<iframe
  src="/api/index.html"
  title="Whoosh-NG API Documentation"
  width="100%"
  height="1200px"
  style={{ border: "none" }}
/>
'''

    en_path = DOCS_EN_DIR / "api" / "reference.md"
    fr_path = DOCS_FR_DIR / "api" / "reference.md"

    en_path.parent.mkdir(parents=True, exist_ok=True)
    fr_path.parent.mkdir(parents=True, exist_ok=True)

    en_path.write_text(md_content, encoding="utf-8")
    print(f"Created: {en_path}")

    # FR version with translated title
    fr_content = md_content.replace(
        'title: "API Reference"',
        'title: "Référence API"',
    ).replace(
        "# API Reference",
        "# Référence API",
    ).replace(
        "auto-generated from source code using",
        "générée automatiquement à partir du code source avec",
    ).replace(
        "which parses Python modules",
        "qui analyse les modules Python",
    ).replace(
        "and generates HTML documentation from docstrings.",
        "et génère une documentation HTML à partir des docstrings.",
    ).replace(
        "Open API Reference",
        "Ouvrir la référence API",
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
