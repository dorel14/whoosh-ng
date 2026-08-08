"""Module de generation des fichiers de documentation LLM (llms.txt et llms-full.txt).

Ce module genere deux fichiers a la racine du depot, consomes par les LLM
et les robots d'indexation :

- ``llms.txt`` -- un index simple avec des liens vers chaque page de la
  documentation Docusaurus (en anglais et en francais).
- ``llms-full.txt`` -- le contenu complet de tous les documents Markdown,
  nettoyé du front-matter YAML.

Auteur: SoniqueBay Team
Version: 2.0.0 (Docusaurus migration)
"""

from __future__ import annotations

import re
from pathlib import Path

# Configuration
DOCS_DIR = Path("website/docs")
DOCS_FR_DIR = Path("website/i18n/fr/docusaurus-plugin-content-docs/current")
EXAMPLES_DIR = Path("docs/archive_jekyll/_en/examples")
OUTPUT_INDEX = Path("llms.txt")
OUTPUT_FULL = Path("llms-full.txt")
OUTPUT_INDEX_STATIC = Path("website/static/llms.txt")
OUTPUT_FULL_STATIC = Path("website/static/llms-full.txt")

# GitHub Pages base URL
BASE_URL = "https://dorel14.github.io/whoosh-ng"


def clean_front_matter(content: str) -> str:
    """Nettoie le contenu Markdown en supprimant le front-matter YAML
    et les attributs de classe kramdown.
    """
    content = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)
    content = re.sub(r"\{:.*?\}", "", content)
    return content.strip()


def _doc_url(doc_path: Path, locale: str) -> str:
    """Convertit un chemin de fichier Markdown en URL Docusaurus.

    - EN: website/docs/core/installation.md -> /whoosh-ng/core/installation
    - FR: website/i18n/fr/.../core/installation.md -> /whoosh-ng/fr/core/installation
    """
    content = doc_path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    slug = None
    if fm_match:
        fm = fm_match.group(1)
        slug_match = re.search(r"^slug:\s*(.*)$", fm, re.MULTILINE)
        if slug_match:
            slug = slug_match.group(1).strip()

    if slug:
        slug_path = slug.strip("/")
        if not slug_path:
            return f"{BASE_URL}/" if locale == "en" else f"{BASE_URL}/{locale}/"
        return f"{BASE_URL}/{slug_path}" if locale == "en" else f"{BASE_URL}/{locale}/{slug_path}"

    # Fallback: derive from file path
    rel = doc_path.relative_to(DOCS_DIR) if locale == "en" else doc_path.relative_to(DOCS_FR_DIR)
    rel_posix = rel.with_suffix("").as_posix()
    return f"{BASE_URL}/{locale}/{rel_posix}/"


def _title_from_path(md_file: Path) -> str:
    """Extrait un titre lisible a partir du nom de fichier."""
    return md_file.stem.replace("-", " ").replace("_", " ").title()


def generate() -> None:
    """Genere ``llms.txt`` (index) et ``llms-full.txt`` (corpus complet)."""
    full_md: list[str] = ["# whoosh-ng : Full Technical Documentation\n"]
    index_md: list[str] = [
        "# whoosh-ng\n",
        "> Documentation technique complete pour whoosh-ng.\n",
        "## Core Documentation\n",
    ]

    # --- EN Markdown ---
    if DOCS_DIR.exists():
        for md_file in sorted(DOCS_DIR.rglob("*.md")):
            if md_file.name == "index.md":
                continue
            content = md_file.read_text(encoding="utf-8")
            clean_content = clean_front_matter(content)
            title = _title_from_path(md_file)
            url = _doc_url(md_file, "en")
            index_md.append(f"- [{title}]({url})")
            full_md.append(f"\n\n## DOCUMENT: {title}\n")
            full_md.append(clean_content)

    # --- FR Markdown ---
    index_md.append("\n## Documentation Française\n")
    if DOCS_FR_DIR.exists():
        for md_file in sorted(DOCS_FR_DIR.rglob("*.md")):
            if md_file.name == "index.md":
                continue
            content = md_file.read_text(encoding="utf-8")
            clean_content = clean_front_matter(content)
            title = _title_from_path(md_file)
            url = _doc_url(md_file, "fr")
            index_md.append(f"- [{title}]({url})")
            full_md.append(f"\n\n## DOCUMENT (FR): {title}\n")
            full_md.append(clean_content)

    # --- Code Examples ---
    index_md.append("\n## Code Examples & Recipes\n")
    full_md.append("\n\n# Code Examples\n")
    if EXAMPLES_DIR.exists():
        for py_file in sorted(EXAMPLES_DIR.glob("*.py")):
            code = py_file.read_text(encoding="utf-8")
            full_md.append(f"\n### Example: {py_file.name}\n")
            full_md.append(f"```python\n{code}\n```")
            github_url = f"https://github.com/dorel14/whoosh-ng/blob/master/docs/archive_jekyll/_en/examples/{py_file.name}"
            index_md.append(f"- [Example: {py_file.name}]({github_url})")

    OUTPUT_INDEX.write_text("\n".join(index_md), encoding="utf-8")
    OUTPUT_FULL.write_text("\n".join(full_md), encoding="utf-8")
    # Also copy to static/ for Docusaurus to serve
    OUTPUT_INDEX_STATIC.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_INDEX_STATIC.write_text("\n".join(index_md), encoding="utf-8")
    OUTPUT_FULL_STATIC.write_text("\n".join(full_md), encoding="utf-8")
    print(f"Fichiers {OUTPUT_INDEX} et {OUTPUT_FULL} generes avec succes.")


if __name__ == "__main__":
    generate()
