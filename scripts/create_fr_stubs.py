#!/usr/bin/env python3
"""Create FR stubs for missing API documentation pages.

NOTE: This logic is now integrated into ``migrate_to_docusaurus.py``.
This standalone script is kept for backward compatibility but the
migration script is the canonical source.

Module de creation des stubs FR pour les pages d'API manquantes.

Note: Cette logique est maintenant integrée dans ``migrate_to_docusaurus.py``.
Ce script autonome est conservé pour la compatibilité ascendante.
"""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_EN_DIR = REPO_ROOT / "docs" / "archive_jekyll" / "_en"
FR_BASE = REPO_ROOT / "website" / "i18n" / "fr" / "docusaurus-plugin-content-docs" / "current"

# Missing FR API docs (exist in EN but not in FR)
FR_MISSING_API: list[str] = [
    "api/analysis.md",
    "api/highlight.md",
    "api/spelling.md",
    "api/sorting.md",
    "api/collectors.md",
    "api/reading.md",
    "api/matching.md",
    "api/codecs.md",
    "api/formats.md",
    "api/columns.md",
    "api/idsets.md",
    "api/automata.md",
    "api/classify.md",
    "api/lang.md",
    "api/filedb_storage.md",
]

# Also add the missing FR core and modern docs to the sidebars
FR_MISSING_CORE: list[str] = [
    "core/dates.md",
    "core/nested.md",
    "core/glossary.md",
    "core/translation-status.md",
    "core/sorting.md",
    "core/auto-indexing.md",
]
FR_MISSING_MODERN: list[str] = [
    "modern/stemming.md",
    "modern/ngrams.md",
    "modern/storage-providers.md",
]

# All missing FR docs
all_fr_missing = FR_MISSING_API + FR_MISSING_CORE + FR_MISSING_MODERN

# Check which ones already exist
existing_stubs = []
for rel in all_fr_missing:
    dst = FR_BASE / rel
    if dst.exists():
        existing_stubs.append(rel)

print("Already existing FR stubs:")
for s in existing_stubs:
    print(f"  {s}")

print(f"\nNeed to create: {len(all_fr_missing) - len(existing_stubs)} stubs")

# Also check if these docs are in the FR sidebar
# We need to update the sidebar to include them
# But actually, the sidebar already references them (since it uses the same sidebars.ts)
# We just need the files to exist
for rel in all_fr_missing:
    dst = FR_BASE / rel
    if dst.exists():
        continue
    en_src = DOCS_EN_DIR / rel
    if en_src.exists():
        en_content = en_src.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\n(.*?)\n---\n(.*)", en_content, re.DOTALL)
        if fm_match:
            en_fm = fm_match.group(1)
            en_body = fm_match.group(2)
            en_title_m = re.search(r'^title:\s*(.*)$', en_fm, re.MULTILINE)
            en_title = en_title_m.group(1).strip().strip('"') if en_title_m else "Untitled"
            en_nav_m = re.search(r'^nav_order:\s*(\d+)$', en_fm, re.MULTILINE)
            en_nav = en_nav_m.group(1) if en_nav_m else "100"

            stub_fm = f"title: {en_title!r}\nsidebar_position: {en_nav}"
            # Convert links in body
            # Simple conversion for FR stubs: replace /en/ with / and /fr/ with /fr/
            stub_body = en_body
            # Replace Jekyll Liquid links
            stub_body = re.sub(
                r"\(\{\{\s*['\"]([^'\"]+)['\"]\s*\|\s*relative_url\s*\}\}\)",
                lambda m: ")(/" + m.group(1).strip("/").replace("en/", "").replace("fr/", "fr/").rstrip("/") + ")",
                stub_body
            )
            stub_body = re.sub(r"\{:.*?\}", "", stub_body)

            stub = f"""---
{stub_fm}
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
> Le contenu anglais est affiché ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->

{stub_body}
"""
        else:
            stub = f'''---
title: "{rel}"
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
'''
    else:
        stub = f'''---
title: "{rel}"
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
'''
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(stub, encoding="utf-8")
    print(f"  Created FR stub: {rel}")

print(f"\nDone. Total missing FR docs: {len(all_fr_missing)}")
