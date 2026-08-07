"""Module de génération des fichiers de documentation LLM (llms.txt et llms-full.txt).

Ce module génère deux fichiers à la racine du dépôt, consommés par les LLM
et les robots d'indexation :

- ``llms.txt`` — un index simple avec des liens vers chaque page de la
  documentation Jekyll (en anglais et en français).
- ``llms-full.txt`` — le contenu complet de tous les documents Markdown et
  exemples Python, nettoyé des balises Jekyll/Liquid.

Auteur: SoniqueBay Team
Version: 1.0.0
"""

from __future__ import annotations

import re
from pathlib import Path

# Configuration
DOCS_DIR = Path("docs")
EXAMPLES_DIR = Path("examples")
OUTPUT_INDEX = Path("llms.txt")
OUTPUT_FULL = Path("llms-full.txt")

# GitHub Pages base URL (lowercase repo name, baseurl from _config.yml)
BASE_URL = "https://dorel14.github.io/whoosh-ng"


def clean_jekyll_markdown(content: str) -> str:
    """Nettoie le contenu Markdown en supprimant les éléments spécifiques à Jekyll.

    Supprime le *front-matter* YAML, les tags Liquid (``{% ... %}``) et les
    attributs de classe kramdown (``{: ... }``).
    """
    # 1. Supprimer le front-matter YAML (entre les deux ---)
    content = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)
    # 2. Supprimer les tags Liquid Jekyll {% ... %}
    content = re.sub(r"\{%.*?%\}", "", content)
    # 3. Supprimer les attributs de classe kramdown {: .note }
    content = re.sub(r"\{:.*?\}", "", content)
    return content.strip()


def _doc_rel_url(md_file: Path) -> str:
    """Convertit un chemin de fichier Markdown relatif à ``docs/`` en URL Jekyll.

    Exemple : ``_en/guides/core-concepts.md`` → ``/en/guides/core-concepts/``
    """
    rel = md_file.relative_to(DOCS_DIR)
    # On retire l'extension .md et on ajoute un slash final pour le permalien *pretty*
    rel_posix = rel.with_suffix("").as_posix()
    # Les dossiers _en → /en/, _fr → /fr/
    rel_posix = rel_posix.replace("_en", "en").replace("_fr", "fr")
    return f"/{rel_posix}/"


def _title_from_path(md_file: Path) -> str:
    """Extrait un titre lisible à partir du nom de fichier."""
    return md_file.stem.replace("-", " ").replace("_", " ").title()


def generate() -> None:
    """Génère ``llms.txt`` (index) et ``llms-full.txt`` (corpus complet).

    Parcourt tous les fichiers Markdown sous ``docs/`` (sauf ``docs/index.md``
    qui est la page d'accueil) et, le cas échéant, tous les scripts Python sous
    ``examples/``.
    """
    full_md: list[str] = ["# whoosh-ng : Full Technical Documentation\n"]
    index_md: list[str] = [
        "# whoosh-ng\n",
        "> Documentation technique complète pour whoosh-ng.\n",
        "## Core Documentation\n",
    ]

    # --- Section 1 : Documentation Markdown ---
    for md_file in sorted(DOCS_DIR.rglob("*.md")):
        # Skip the root index.md — it's just a language selector
        if md_file.name == "index.md" and md_file.parent == DOCS_DIR:
            continue

        with md_file.open("r", encoding="utf-8") as f:
            raw_content = f.read()

        clean_content = clean_jekyll_markdown(raw_content)
        title = _title_from_path(md_file)
        url = _doc_rel_url(md_file)
        full_url = f"{BASE_URL}{url}"

        index_md.append(f"- [{title}]({full_url})")
        full_md.append(f"\n\n## DOCUMENT: {title}\n")
        full_md.append(clean_content)

    # --- Section 2 : Code Examples ---
    index_md.append("\n## Code Examples & Recipes\n")
    full_md.append("\n\n# Code Examples\n")

    if EXAMPLES_DIR.exists():
        for py_file in sorted(EXAMPLES_DIR.glob("*.py")):
            with py_file.open("r", encoding="utf-8") as f:
                code = f.read()
            full_md.append(f"\n### Example: {py_file.name}\n")
            full_md.append(f"```python\n{code}\n```")
            github_url = f"https://github.com/dorel14/whoosh-ng/blob/master/examples/{py_file.name}"
            index_md.append(f"- [Example: {py_file.name}]({github_url})")

    # --- Écriture des fichiers ---
    OUTPUT_INDEX.write_text("\n".join(index_md), encoding="utf-8")
    OUTPUT_FULL.write_text("\n".join(full_md), encoding="utf-8")
    print(f"Fichiers {OUTPUT_INDEX} et {OUTPUT_FULL} générés avec succès.")


if __name__ == "__main__":
    generate()
