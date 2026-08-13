#!/usr/bin/env python3
"""Audit FR documentation for untranslated content."""

import re
from pathlib import Path

fr_dir = Path("website/i18n/fr/docusaurus-plugin-content-docs/current")
en_dir = Path("website/docs")

# English marker patterns that indicate untranslated content
english_markers = [
    r"\bthe\b",
    r"\band\b",
    r"\bis\b",
    r"\bare\b",
    r"\bto\b",
    r"\bof\b",
    r"\bin\b",
    r"\bfor\b",
    r"\bwith\b",
    r"\bThis\b",
    r"Whoosh-NG Documentation",
]

fr_files = sorted(fr_dir.rglob("*.md"))
print(f"Total FR files: {len(fr_files)}")
en_count = len(list(en_dir.rglob("*.md")))
print(f"Total EN files: {en_count}")
print()

untranslated = []
stubs: list[str] = []
for fr_file in fr_files:
    content = fr_file.read_text(encoding="utf-8")
    rel = fr_file.relative_to(fr_dir)

    # Count English marker matches
    eng_count = sum(len(re.findall(p, content, re.IGNORECASE)) for p in english_markers)

    # Check for stub translation notice
    is_stub = (
        "TRADUCTION" in content
        or "Traduit automatiquement" in content
        or "EN COURS DE TRADUCTION" in content
    )

    # Check if FR file has any French-specific characters
    has_french = bool(re.search(r"[àâäéèêëïîôöùûüÿç]", content))

    if eng_count > 50:
        label = "STUB" if is_stub else "UNTRANSLATED"
        untranslated.append((label, eng_count, rel))
    elif eng_count > 20 and not has_french:
        untranslated.append(("UNTRANSLATED", eng_count, rel))

untranslated.sort(key=lambda x: x[1], reverse=True)
print("=== Files with significant English content ===")
for label, count, path in untranslated:
    print(f"  {label:12} eng_matches={count:4d}  {path}")

if not untranslated:
    print("  (none found)")
