#!/usr/bin/env python3
"""Migration script: Jekyll -> Docusaurus for Whoosh-NG documentation.

Performs the full migration described in .kilo/plans/1786286919345-jekyll-to-docusaurus-migration.md

Strategy (simplified — no SEO slug preservation):
  - Files keep their natural Docusaurus path structure (core/, modern/, api/, examples/)
  - Jekyll permalinks are dropped; Docusaurus derives URLs from file paths
  - Jekyll links {{ '/en/guides/X/' | relative_url }} are converted to
    /core/X or /modern/X based on the file's actual location
  - Jekyll links {{ '/en/quickstart/' | relative_url }} -> /core/quickstart
  - Jekyll links {{ '/en/api/X/' | relative_url }} -> /api/X
  - Jekyll links {{ '/en/examples/X/' | relative_url }} -> /examples/X
  - Jekyll links {{ '/en/' | relative_url }} -> / (homepage = intro.md)
  - Jekyll links {{ '/fr/...' | relative_url }} -> same but with /fr/ prefix
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
DOCS_ARCHIVE = DOCS_DIR / "archive_jekyll"
WEBSITE_DIR = REPO_ROOT / "website"
DOCS_EN_DIR = DOCS_ARCHIVE / "_en"
DOCS_FR_DIR = DOCS_ARCHIVE / "_fr"


# ─── Guide name → Docusaurus path mapping ─────────────────────────────────────
# The old Jekyll links use /guides/X/ for files that are now in core/ or modern/.
# This mapping resolves guide names to their new Docusaurus paths.

EN_GUIDE_MAP: dict[str, str] = {
    "quickstart": "core/quickstart",
    "installation": "core/installation",
    "core-concepts": "core/core-concepts",
    "indexing": "core/indexing",
    "searching": "core/searching",
    "schema": "core/schema",
    "query": "core/query",
    "backends": "core/backends",
    "dates": "core/dates",
    "nested": "core/nested",
    "sorting": "core/sorting",
    "auto-indexing": "core/auto-indexing",
    "glossary": "core/glossary",
    "migration": "core/migration",
    "legacy-cleanup": "core/legacy-cleanup",
    "translation-status": "core/translation-status",
    "middleware": "modern/middleware",
    "middleware-pipeline": "modern/middleware-pipeline",
    "plugins": "modern/plugins",
    "plugins-advanced": "modern/plugins-advanced",
    "autocomplete": "modern/autocomplete",
    "autocomplete-providers": "modern/autocomplete-providers",
    "vector": "modern/vector",
    "modern-indexing": "modern/modern-indexing",
    "monitoring": "modern/monitoring",
    "performance": "modern/performance",
    "linguistics": "modern/linguistics",
    "stemming": "modern/stemming",
    "stemming-providers": "modern/stemming-providers",
    "ngrams": "modern/ngrams",
    "storage-providers": "modern/storage-providers",
    "provider-integration": "modern/provider-integration",
}


def _resolve_guide(guide_name: str, locale: str) -> str:
    """Resolve a guide name to its Docusaurus internal URL.

    In Docusaurus i18n, the locale prefix is added automatically,
    so the URL does not include the locale prefix.
    """
    if guide_name in EN_GUIDE_MAP:
        doc_path = EN_GUIDE_MAP[guide_name]
        return f"/{doc_path}"
    # Fallback: use the guide name as-is
    return f"/guides/{guide_name}"


# ─── Build permalink -> Docusaurus URL map ─────────────────────────────────────


def _build_permalink_map(locale: str) -> dict[str, str]:
    """Scan source files and build permalink -> Docusaurus URL map.

    /en/guides/installation/  ->  /core/installation
    /en/quickstart/           ->  /core/quickstart
    /en/api/overview/         ->  /api/overview
    /en/                      ->  /
    """
    src_dir = DOCS_EN_DIR if locale == "en" else DOCS_FR_DIR
    pmap: dict[str, str] = {}

    for md in sorted(src_dir.rglob("*.md")):
        rel = md.relative_to(src_dir)
        rel_posix = rel.with_suffix("").as_posix()
        content = md.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)

        permalink = None
        if fm_match:
            fm = fm_match.group(1)
            pm = re.search(r"^permalink:\s*(.*)$", fm, re.MULTILINE)
            if pm:
                permalink = pm.group(1).strip().strip('"').strip("'")

        if permalink:
            # Use the permalink as the key, map to the Docusaurus-internal URL.
            # In Docusaurus i18n, the locale prefix is added automatically.
            # So the URL is the same for all locales:
            #    /en/guides/installation/ -> /core/installation
            #    /fr/guides/installation/ -> /core/installation
            # Docusaurus resolves /core/installation -> /fr/core/installation
            # when serving the FR locale.
            if rel_posix == "index":
                pmap[permalink] = "/"
            else:
                pmap[permalink] = f"/{rel_posix}"
        else:
            # No permalink — derive from file path
            # _en/api/overview.md -> /en/api/overview/ -> /api/overview
            # _fr/api/overview.md -> /fr/api/overview/ -> /api/overview
            if rel_posix == "index":
                key = f"/{locale}/"
                pmap[key] = "/"
            else:
                key = f"/{locale}/{rel_posix}/"
                pmap[key] = f"/{rel_posix}"

    return pmap


EN_PERMALINK_MAP = _build_permalink_map("en")
FR_PERMALINK_MAP = _build_permalink_map("fr")


# ─── Link conversion ──────────────────────────────────────────────────────────

LIQUID_URL_RE = re.compile(r"\{\{\s*['\"]([^'\"]+)['\"]\s*\|\s*relative_url\s*\}\}")


def convert_links(content: str, locale: str, is_stub: bool = False) -> str:
    """Convert all Jekyll Liquid URL tags to Docusaurus URLs.

    Args:
        content: The markdown content to process.
        locale: The target locale ('en' or 'fr').
        is_stub: If True, this is a FR stub file using EN content —
                 cross-locale links should be converted to the current
                 locale (e.g. /core/X -> /fr/core/X). If False, cross-locale
                 links use full URLs to avoid Docusaurus broken link errors.
    """
    pmap = EN_PERMALINK_MAP if locale == "en" else FR_PERMALINK_MAP

    def _replace(match: re.Match) -> str:
        path: str = match.group(1)
        # Handle llms.txt / llms-full.txt — served from static/
        if path in ("/llms.txt", "/llms-full.txt"):
            return path
        # Handle /changelog/
        if path in ("/changelog/", "/changelog"):
            return "https://github.com/dorel14/whoosh-ng/blob/master/CHANGELOG.md"
        # Handle links to non-existent top-level indexes
        if path in (
            "/en/examples/",
            "/fr/examples/",
            "/examples/",
            "/en/api/",
            "/fr/api/",
            "/api/",
            "/en/modern/",
            "/fr/modern/",
            "/modern/",
            "/en/core/",
            "/fr/core/",
            "/core/",
        ):
            # Map /fr/examples/ -> /examples/basic-indexing, etc.
            # Strip locale prefix (en/ or fr/) from the path first
            raw = path.strip("/")
            if raw.startswith("en/") or raw.startswith("fr/"):
                raw = raw[3:]
            section = raw.split("/")[0]
            section_redirects = {
                "examples": "/examples/basic-indexing",
                "api": "/api/overview",
                "core": "/core/quickstart",
                "modern": "/modern/middleware",
            }
            if section in section_redirects:
                return section_redirects[section]
        # Handle links to non-existent pages
        migration_paths = (
            "/en/examples/migration/",
            "/fr/examples/migration/",
            "/examples/migration/",
            "/examples/migration",
        )
        if path in migration_paths:
            return (
                "https://github.com/dorel14/whoosh-ng/tree/master/docs/archive_jekyll/_en/examples"
            )
        # Direct lookup in the current locale's permalink map
        if path in pmap:
            return pmap[path]
        # Try with locale prefix stripped (rebuild key)
        stripped = path.strip("/")
        key = f"/{locale}/{stripped}/" if stripped else f"/{locale}/"
        if key in pmap:
            return pmap[key]
        # Try cross-locale lookup (EN docs linking to /fr/ or vice versa)
        other_locale = "fr" if locale == "en" else "en"
        other_map = FR_PERMALINK_MAP if locale == "en" else EN_PERMALINK_MAP
        cross_link: str | None = None
        if path in other_map:
            cross_link = other_map[path]
        else:
            key2 = f"/{other_locale}/{stripped}/" if stripped else f"/{other_locale}/"
            if key2 in other_map:
                cross_link = other_map[key2]
        if cross_link is not None:
            if is_stub and locale == "fr":
                # FR stub: cross_link is already a /doc/path URL (without locale).
                # Docusaurus adds the locale prefix automatically.
                return cross_link
            else:
                # Real cross-locale link: use full URL
                return f"https://dorel14.github.io/whoosh-ng{cross_link}"
        # Fallback: rebuild from path
        if stripped in ("en", "fr", ""):
            return "/"
        # Remove locale prefix if still present
        if stripped.startswith(f"{locale}/"):
            stripped = stripped[len(f"{locale}/") :]
        if stripped.startswith("en/") or stripped.startswith("fr/"):
            stripped = stripped[3:]
        # /guides/X/ -> /core/X or /modern/X (lookup by guide name)
        if stripped.startswith("guides/"):
            guide_name = stripped[len("guides/") :]
            return _resolve_guide(guide_name, locale)
        # Bare /guides/ -> /core/ (the Core index page)
        if stripped == "guides":
            return "/core"
        return f"/{stripped}"

    return LIQUID_URL_RE.sub(_replace, content)


def rewrite_internal_links(content: str, locale: str) -> str:
    """No-op for FR stubs.

    In Docusaurus i18n, internal links without locale prefix are resolved
    automatically by prepending the locale. So /core/quickstart works in both
    EN (/core/quickstart) and FR (/fr/core/quickstart) locales.

    This function is kept for compatibility but does nothing.
    """
    if locale == "en":
        return content

    # In Docusaurus, internal links like /core/quickstart are automatically
    # resolved to /fr/core/quickstart for the FR locale. No rewriting needed.
    return content


# ─── Front matter conversion ──────────────────────────────────────────────────


def process_front_matter(fm_text: str, locale: str) -> str:
    """Convert Jekyll front matter keys to Docusaurus equivalents.

    - permalink  -> dropped (Docusaurus uses file path)
    - nav_order   -> sidebar_position
    - lang: fr    -> dropped (handled by i18n)
    - has_children -> dropped (handled by sidebars.ts)
    """
    lines = fm_text.strip().split("\n")
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("permalink:"):
            continue
        elif stripped.startswith("nav_order:"):
            val = stripped.split(":", 1)[1].strip()
            new_lines.append(f"sidebar_position: {val}")
        elif stripped.startswith("lang:") or stripped.startswith("has_children:"):
            continue
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


def escape_mdx_lt(content: str) -> str:
    """Escape < characters that look like JSX tags to MDX parser.

    In Jekyll (kramdown), bare < characters are fine, but in MDX (used by
    Docusaurus), < followed by a letter/digit is interpreted as a JSX tag.
    This function escapes < that are used as comparison operators (e.g. <100k)
    while preserving real HTML tags and code blocks.

    Only escapes < followed by a digit or space+number (comparison operators).
    """
    lines = content.split("\n")
    new_lines: list[str] = []
    in_code_block = False
    for line in lines:
        # Skip lines inside code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            new_lines.append(line)
            continue
        if in_code_block:
            new_lines.append(line)
            continue
        # Replace < followed by a digit or < with space+digit (comparison operators)
        # e.g. "<100k" -> "&lt;100k", "< 100" -> "&lt; 100"
        line = re.sub(r"<(\d)", r"&lt;\1", line)
        line = re.sub(r"< (\d)", r"&lt; \1", line)
        # Also handle > followed by a digit (could cause issues)
        # but > is generally safe in MDX
        new_lines.append(line)
    return "\n".join(new_lines)


def migrate_file(src: Path, dst: Path, locale: str) -> None:
    """Migrate a single markdown file from Jekyll to Docusaurus format."""
    content = src.read_text(encoding="utf-8")

    fm_match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if not fm_match:
        new_content = convert_links(content, locale)
        new_content = escape_mdx_lt(new_content)
        new_content = re.sub(r"\{:.*?\}", "", new_content)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(new_content, encoding="utf-8")
        return

    fm = fm_match.group(1)
    body = fm_match.group(2)

    new_fm = process_front_matter(fm, locale)
    new_body = convert_links(body, locale)
    new_body = escape_mdx_lt(new_body)
    new_body = re.sub(r"\{:.*?\}", "", new_body)

    new_content = f"---\n{new_fm}\n---\n{new_body}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(new_content, encoding="utf-8")


# ─── File mappings ────────────────────────────────────────────────────────────

# EN: source path (relative to docs/_en/) -> destination path (relative to website/docs/)
EN_FILE_MAP: dict[str, str] = {
    "index.md": "intro.md",
    "core/index.md": "core/index.md",
    "core/quickstart.md": "core/quickstart.md",
    "core/installation.md": "core/installation.md",
    "core/core-concepts.md": "core/core-concepts.md",
    "core/indexing.md": "core/indexing.md",
    "core/searching.md": "core/searching.md",
    "core/schema.md": "core/schema.md",
    "core/query.md": "core/query.md",
    "core/backends.md": "core/backends.md",
    "core/dates.md": "core/dates.md",
    "core/nested.md": "core/nested.md",
    "core/sorting.md": "core/sorting.md",
    "core/auto-indexing.md": "core/auto-indexing.md",
    "core/glossary.md": "core/glossary.md",
    "core/migration.md": "core/migration.md",
    "core/legacy-cleanup.md": "core/legacy-cleanup.md",
    "core/translation-progress.md": "core/translation-progress.md",
    "modern/index.md": "modern/index.md",
    "modern/middleware.md": "modern/middleware.md",
    "modern/middleware-pipeline.md": "modern/middleware-pipeline.md",
    "modern/plugins.md": "modern/plugins.md",
    "modern/plugins-advanced.md": "modern/plugins-advanced.md",
    "modern/autocomplete.md": "modern/autocomplete.md",
    "modern/autocomplete-providers.md": "modern/autocomplete-providers.md",
    "modern/vector.md": "modern/vector.md",
    "modern/modern-indexing.md": "modern/modern-indexing.md",
    "modern/monitoring.md": "modern/monitoring.md",
    "modern/performance.md": "modern/performance.md",
    "modern/linguistics.md": "modern/linguistics.md",
    "modern/stemming.md": "modern/stemming.md",
    "modern/stemming-providers.md": "modern/stemming-providers.md",
    "modern/ngrams.md": "modern/ngrams.md",
    "modern/storage-providers.md": "modern/storage-providers.md",
    "modern/provider-integration.md": "modern/provider-integration.md",
    "api/overview.md": "api/overview.md",
    "api/core.md": "api/core.md",
    "api/fields.md": "api/fields.md",
    "api/analysis.md": "api/analysis.md",
    "api/highlight.md": "api/highlight.md",
    "api/spelling.md": "api/spelling.md",
    "api/sorting.md": "api/sorting.md",
    "api/collectors.md": "api/collectors.md",
    "api/reading.md": "api/reading.md",
    "api/matching.md": "api/matching.md",
    "api/codecs.md": "api/codecs.md",
    "api/formats.md": "api/formats.md",
    "api/columns.md": "api/columns.md",
    "api/idsets.md": "api/idsets.md",
    "api/automata.md": "api/automata.md",
    "api/classify.md": "api/classify.md",
    "api/lang.md": "api/lang.md",
    "api/filedb_storage.md": "api/filedb_storage.md",
    "api/writing.md": "api/writing.md",
    "api/searching.md": "api/searching.md",
    "api/query.md": "api/query.md",
    "api/events.md": "api/events.md",
    "api/middleware.md": "api/middleware.md",
    "api/plugins.md": "api/plugins.md",
    "api/backends.md": "api/backends.md",
    "api/modern.md": "api/modern.md",
    "examples/basic-indexing.md": "examples/basic-indexing.md",
    "examples/search.md": "examples/search.md",
    "examples/search-models.md": "examples/search-models.md",
    "examples/fastapi-search.md": "examples/fastapi-search.md",
    "examples/middleware.md": "examples/middleware.md",
    "examples/middleware-pipeline.md": "examples/middleware-pipeline.md",
    "examples/movie-search.md": "examples/movie-search.md",
    "examples/plugin-dev.md": "examples/plugin-dev.md",
    "examples/data-sources.md": "examples/data-sources.md",
    "examples/schema-discovery.md": "examples/schema-discovery.md",
    "examples/facets.md": "examples/facets.md",
    "examples/validation.md": "examples/validation.md",
    "examples/search-view.md": "examples/search-view.md",
    "examples/autocomplete.md": "examples/autocomplete.md",
    "examples/vector-search.md": "examples/vector-search.md",
}

# EN files that don't exist as sources — need stubs
EN_STUBS: dict[str, str] = {
    "core/sorting.md": """---
title: "Sorting"
sidebar_position: 26
---

# Sorting

The `whoosh.sorting` module provides facets and sort-key computation for ordering and
grouping search results.

## Quick start

```python
from whoosh import sorting

# Sort by a field
results = searcher.search(query, sortedby="date")

# Sort descending
results = searcher.search(query, sortedby=sorting.FieldFacet("price", reverse=True))
```

For the full API reference, see [Sorting API](/api/sorting).
""",
    "core/auto-indexing.md": """---
title: "Auto-Indexing"
sidebar_position: 27
---

# Auto-Indexing

Whoosh-NG provides utilities for automatic schema discovery and data-source driven indexing.

## Schema Discovery

The `SchemaDiscovery` utility inspects a data source and auto-generates a Whoosh schema:

```python
from whoosh_modern.discovery import SchemaDiscovery

discovery = SchemaDiscovery(source=data_source)
schema = discovery.discover()
```

See [SearchView](/examples/search-view) and [Data Sources](/examples/data-sources) for
usage examples.
""",
}

# FR: only files that exist in FR
FR_FILE_MAP: dict[str, str] = {
    "index.md": "intro.md",
    "core/index.md": "core/index.md",
    "core/quickstart.md": "core/quickstart.md",
    "core/installation.md": "core/installation.md",
    "core/core-concepts.md": "core/core-concepts.md",
    "core/indexing.md": "core/indexing.md",
    "core/searching.md": "core/searching.md",
    "core/schema.md": "core/schema.md",
    "core/query.md": "core/query.md",
    "core/backends.md": "core/backends.md",
    "core/migration.md": "core/migration.md",
    "core/legacy-cleanup.md": "core/legacy-cleanup.md",
    "modern/index.md": "modern/index.md",
    "modern/middleware.md": "modern/middleware.md",
    "modern/middleware-pipeline.md": "modern/middleware-pipeline.md",
    "modern/plugins.md": "modern/plugins.md",
    "modern/plugins-advanced.md": "modern/plugins-advanced.md",
    "modern/autocomplete.md": "modern/autocomplete.md",
    "modern/autocomplete-fournisseurs.md": "modern/autocomplete-fournisseurs.md",
    "modern/vector.md": "modern/vector.md",
    "modern/modern-indexing.md": "modern/modern-indexing.md",
    "modern/monitoring.md": "modern/monitoring.md",
    "modern/performance.md": "modern/performance.md",
    "modern/linguistique.md": "modern/linguistique.md",
    "modern/stemmers-fournisseurs.md": "modern/stemmers-fournisseurs.md",
    "api/overview.md": "api/overview.md",
    "api/core.md": "api/core.md",
    "api/fields.md": "api/fields.md",
    "api/middleware.md": "api/middleware.md",
    "api/plugins.md": "api/plugins.md",
    "api/backends.md": "api/backends.md",
    "api/query.md": "api/query.md",
    "api/searching.md": "api/searching.md",
    "api/events.md": "api/events.md",
    "api/writing.md": "api/writing.md",
    "api/modern.md": "api/modern.md",
    "examples/autocomplete.md": "examples/autocomplete.md",
    "examples/basic-indexing.md": "examples/basic-indexing.md",
    "examples/data-sources.md": "examples/data-sources.md",
    "examples/facets.md": "examples/facets.md",
    "examples/fastapi-search.md": "examples/fastapi-search.md",
    "examples/middleware.md": "examples/middleware.md",
    "examples/middleware-pipeline.md": "examples/middleware-pipeline.md",
    "examples/movie-search.md": "examples/movie-search.md",
    "examples/plugin-dev.md": "examples/plugin-dev.md",
    "examples/schema-discovery.md": "examples/schema-discovery.md",
    "examples/search.md": "examples/search.md",
    "examples/search-models.md": "examples/search-models.md",
    "examples/search-view.md": "examples/search-view.md",
    "examples/validation.md": "examples/validation.md",
    "examples/vector-search.md": "examples/vector-search.md",
}

# Missing FR files — create stubs with EN fallback content
FR_MISSING: list[str] = [
    "core/dates.md",
    "core/nested.md",
    "core/glossary.md",
    "core/translation-progress.md",
    "core/sorting.md",
    "core/auto-indexing.md",
    "modern/stemming.md",
    "modern/ngrams.md",
    "modern/storage-providers.md",
    # Missing FR API docs (exist in EN but not FR)
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


# ─── Site config files ────────────────────────────────────────────────────────


def create_website_scaffold() -> None:
    """Lot A: Create the Docusaurus website directory and config files."""
    if WEBSITE_DIR.exists():
        shutil.rmtree(WEBSITE_DIR)
    WEBSITE_DIR.mkdir(parents=True)

    # package.json
    (WEBSITE_DIR / "package.json").write_text(
        """{
  "name": "whoosh-ng-docs",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "build": "docusaurus build",
    "start": "docusaurus start",
    "write-translations": "docusaurus write-translations",
    "serve": "docusaurus serve"
  },
  "dependencies": {
    "@docusaurus/core": "^3.7.0",
    "@docusaurus/preset-classic": "^3.7.0",
    "@mdx-js/react": "^3.0.0",
    "clsx": "^2.1.0",
    "prism-react-renderer": "^2.4.1",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@docusaurus/types": "^3.7.0",
    "typescript": "^5.6.0"
  }
}
""",
        encoding="utf-8",
    )

    # docusaurus.config.ts
    config_ts = """import type {Config} from '@docusaurus/types';
import {themes as prismThemes} from 'prism-react-renderer';

const config: Config = {
  title: 'Whoosh-NG Documentation',
  tagline: 'Pure-Python full-text indexing and search library, modernized for 2025+',
  favicon: 'favicon.ico',

  url: 'https://dorel14.github.io',
  baseUrl: '/whoosh-ng/',

  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'fr'],
  },

  presets: [
    [
      '@docusaurus/preset-classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          routeBasePath: '/',
          editUrl: 'https://github.com/dorel14/whoosh-ng/tree/master/website/docs',
        },
        blog: false,
      },
    ],
  ],

  themeConfig: {
    navbar: {
      title: 'Whoosh-NG',
      logo: {
        alt: 'Whoosh-NG Logo',
        src: 'img/logo.png',
      },
      items: [
        {
          to: '/core/quickstart',
          label: 'Core',
          position: 'left',
        },
        {
          to: '/modern/middleware',
          label: 'Modern',
          position: 'left',
        },
        {
          to: '/api/overview',
          label: 'API',
          position: 'left',
        },
        {
          to: '/examples/basic-indexing',
          label: 'Examples',
          position: 'left',
        },
        {
          type: 'localeDropdown',
          position: 'right',
        },
        {
          href: 'https://github.com/dorel14/whoosh-ng',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            { label: 'Core', to: '/core/quickstart' },
            { label: 'Modern', to: '/modern/middleware' },
            { label: 'API Reference', to: '/api/overview' },
            { label: 'Examples', to: '/examples/basic-indexing' },
          ],
        },
        {
          title: 'Community',
          items: [
            { label: 'GitHub', href: 'https://github.com/dorel14/whoosh-ng' },
            { label: 'PyPI', href: 'https://pypi.org/project/whoosh-ng/' },
          ],
        },
      ],
      copyright: 'Whoosh-NG Documentation v4.0.1 | Last updated: 2026-08-07',
    },
    prism: {
      theme: prismThemes.oneLight,
      darkTheme: prismThemes.oneDark,
    },
  },

  onBrokenLinks: 'warn',
  onBrokenAnchors: 'throw',
  onBrokenMarkdownLinks: 'warn',
};

export default config;
"""
    (WEBSITE_DIR / "docusaurus.config.ts").write_text(config_ts, encoding="utf-8")

    # tsconfig.json
    (WEBSITE_DIR / "tsconfig.json").write_text(
        """{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "node",
    "esModuleInterop": true,
    "jsx": "react-jsx",
    "strict": true,
    "lib": ["ES2020"],
    "skipLibCheck": true,
    "baseUrl": ".",
    "outDir": "./build",
    "rootDir": "."
  },
  "include": ["src", "docusaurus.config.ts", "sidebars.ts"],
  "exclude": ["node_modules", "build"]
}
""",
        encoding="utf-8",
    )

    # Empty src/ to keep TypeScript happy
    (WEBSITE_DIR / "src").mkdir(parents=True, exist_ok=True)
    (WEBSITE_DIR / "src" / "components").mkdir(parents=True, exist_ok=True)

    # .nojekyll
    (WEBSITE_DIR / ".nojekyll").write_text("", encoding="utf-8")

    # Copy static assets
    static_dir = WEBSITE_DIR / "static"
    (static_dir / "img").mkdir(parents=True, exist_ok=True)

    assets = DOCS_ARCHIVE / "assets"
    if (assets / "logo.png").exists():
        shutil.copy2(assets / "logo.png", static_dir / "img" / "logo.png")
        shutil.copy2(assets / "logo.png", static_dir / "logo.png")
    if (assets / "favico.ico").exists():
        shutil.copy2(assets / "favico.ico", static_dir / "favicon.ico")
    if (assets / "architecture.svg").exists():
        shutil.copy2(assets / "architecture.svg", static_dir / "img" / "architecture.svg")
        shutil.copy2(assets / "architecture.svg", static_dir / "img" / "architecture.svg")
        # Create assets/ alias for backward compat
        (static_dir / "assets").mkdir(parents=True, exist_ok=True)
        shutil.copy2(assets / "architecture.svg", static_dir / "assets" / "architecture.svg")

    # Create placeholder llms.txt and llms-full.txt in static/
    (static_dir / "llms.txt").write_text(
        "# whoosh-ng\n\n> Documentation index. "
        "Run `python scripts/generate_llm_docs.py` to regenerate.\n",
        encoding="utf-8",
    )
    (static_dir / "llms-full.txt").write_text(
        "# whoosh-ng - Full Technical Documentation\n\n"
        "> Run `python scripts/generate_llm_docs.py` to regenerate.\n",
        encoding="utf-8",
    )

    print("Lot A: Docusaurus scaffold created at website/")


# ─── Lot B: EN migration ───────────────────────────────────────────────────────


def migrate_en() -> None:
    """Migrate EN content from docs/_en/ -> website/docs/."""
    docs_out = WEBSITE_DIR / "docs"
    docs_out.mkdir(parents=True, exist_ok=True)

    migrated = 0
    for src_rel, dst_rel in EN_FILE_MAP.items():
        src = DOCS_EN_DIR / src_rel
        dst = docs_out / dst_rel
        if src.exists():
            migrate_file(src, dst, "en")
            migrated += 1
        else:
            print(f"  EN source not found: {src_rel}")

    # Create stub files for EN files that don't exist yet
    for stub_rel, stub_content in EN_STUBS.items():
        dst = docs_out / stub_rel
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(stub_content, encoding="utf-8")
            print(f"  EN stub created: {stub_rel}")

    print(f"Lot B: EN content migrated ({migrated} files + {len(EN_STUBS)} stubs)")


# ─── Lot C: FR migration ──────────────────────────────────────────────────────


def migrate_fr() -> None:
    """Migrate FR content from docs/_fr/ -> website/i18n/fr/.../current/."""
    fr_base = WEBSITE_DIR / "i18n" / "fr" / "docusaurus-plugin-content-docs" / "current"
    fr_base.mkdir(parents=True, exist_ok=True)

    migrated = 0
    for src_rel, dst_rel in FR_FILE_MAP.items():
        src = DOCS_FR_DIR / src_rel
        dst = fr_base / dst_rel
        if src.exists():
            migrate_file(src, dst, "fr")
            migrated += 1
        else:
            print(f"  FR source not found: {src_rel}")

    # Create stub files for missing FR translations
    docs_en_out = WEBSITE_DIR / "docs"
    for missing_rel in FR_MISSING:
        dst = fr_base / missing_rel
        if dst.exists():
            continue
        # Try source EN file, then fall back to the migrated EN output
        en_src = DOCS_EN_DIR / missing_rel
        en_src_out = docs_en_out / missing_rel
        en_content = None
        if en_src.exists():
            en_content = en_src.read_text(encoding="utf-8")
        elif en_src_out.exists():
            en_content = en_src_out.read_text(encoding="utf-8")
        if en_content:
            fm_match = re.match(r"^---\n(.*?)\n---\n(.*)", en_content, re.DOTALL)
            if fm_match:
                en_fm = fm_match.group(1)
                en_body = fm_match.group(2)
                en_title_m = re.search(r"^title:\s*(.*)$", en_fm, re.MULTILINE)
                en_title = en_title_m.group(1).strip().strip('"') if en_title_m else "Untitled"
                en_nav_m = re.search(r"^sidebar_position:\s*(\d+)$", en_fm, re.MULTILINE)
                en_nav = en_nav_m.group(1) if en_nav_m else "0"
                # If no nav_order, try permalink-based ordering
                if en_nav == "0":
                    en_permalink_m = re.search(r"^permalink:\s*(.*)$", en_fm, re.MULTILINE)
                    if en_permalink_m:
                        # Assign based on known ordering
                        permalink = en_permalink_m.group(1).strip()
                        # We don't have nav_order, use a high number
                        en_nav = "100"

                stub_fm = f"title: {en_title!r}\nsidebar_position: {en_nav}"
                stub_body = en_body
                stub_body = convert_links(stub_body, "fr", is_stub=True)
                stub_body = re.sub(r"\{:.*?\}", "", stub_body)
                # If the EN source was the already-converted output (not the
                # original Jekyll file), internal links won't have been
                # converted to FR URLs. Rewrite them now.
                if not en_src.exists() and en_src_out.exists():
                    stub_body = rewrite_internal_links(stub_body, "fr")

                stub = f"""---
{stub_fm}
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
> Le contenu anglais est affiché ci-dessous en attendant la traduction.

<!-- Creez une version francaise de ce fichier et supprimez ce message. -->

{stub_body}
"""
            else:
                stub = f"""---
title: "{missing_rel}"
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
"""
        else:
            stub = f"""---
title: "{missing_rel}"
---

> **Note de traduction** : Cette page n'est pas encore traduite en français.
"""
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(stub, encoding="utf-8")

    print(f"Lot C: FR content migrated ({migrated} files) + {len(FR_MISSING)} stubs")


# ─── Sidebars ─────────────────────────────────────────────────────────────────

EN_SIDEBAR = """import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docs: {
    Core: [
      {type: 'doc', id: 'core/index', label: 'Core'},
      'core/quickstart',
      'core/installation',
      {
        type: 'category',
        label: 'Classic Features',
        items: [
          'core/core-concepts',
          'core/indexing',
          'core/searching',
          'core/schema',
          'core/query',
          'core/backends',
          'core/dates',
          'core/nested',
          'core/sorting',
          'core/auto-indexing',
        ],
      },
      {
        type: 'category',
        label: 'Reference',
        items: [
          'core/glossary',
          'core/migration',
          'core/changelog',
          'core/legacy-cleanup',
          'core/translation-status',
        ],
      },
    ],
    Modern: [
      {type: 'doc', id: 'modern/index', label: 'Modern'},
      'modern/middleware',
      'modern/middleware-pipeline',
      'modern/plugins',
      'modern/plugins-advanced',
      'modern/autocomplete',
      'modern/autocomplete-providers',
      'modern/vector',
      'modern/modern-indexing',
      'modern/monitoring',
      'modern/performance',
      'modern/linguistics',
      'modern/stemming',
      'modern/stemming-providers',
      'modern/ngrams',
      'modern/storage-providers',
      'modern/provider-integration',
    ],
    'API Reference': [
      'api/overview',
      'api/reference',
      'api/core',
      {
        type: 'category',
        label: 'Core API',
        items: [
          'api/fields',
          'api/analysis',
          'api/highlight',
          'api/spelling',
          'api/sorting',
          'api/collectors',
          'api/reading',
          'api/matching',
          'api/codecs',
          'api/formats',
          'api/columns',
          'api/idsets',
          'api/automata',
          'api/classify',
          'api/lang',
        ],
      },
      {
        type: 'category',
        label: 'Modern API',
        items: [
          'api/writing',
          'api/searching',
          'api/query',
          'api/events',
          'api/middleware',
          'api/plugins',
          'api/backends',
          'api/filedb_storage',
          'api/modern',
        ],
      },
    ],
    Examples: [
      'examples/basic-indexing',
      'examples/search',
      'examples/search-models',
      'examples/fastapi-search',
      'examples/middleware',
      'examples/middleware-pipeline',
      'examples/movie-search',
      'examples/plugin-dev',
      'examples/data-sources',
      'examples/schema-discovery',
      'examples/facets',
      'examples/validation',
      'examples/search-view',
      'examples/autocomplete',
      'examples/vector-search',
    ],
  },
};

export default sidebars;
"""


# ─── Lot D: Update generate_llm_docs.py ────────────────────────────────────────


def update_llm_docs_script() -> None:
    script_path = REPO_ROOT / "scripts" / "generate_llm_docs.py"

    _llm_doc_header = '"""Module de generation des fichiers \
        de documentation LLM (llms.txt et llms-full.txt).'
    new_script = (
        _llm_doc_header
        + '''

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
    content = re.sub(r"^---\\s*\\n.*?\\n---\\s*\\n", "", content, flags=re.DOTALL)
    content = re.sub(r"\\{:.*?\\}", "", content)
    return content.strip()


def _doc_url(doc_path: Path, locale: str) -> str:
    """Convertit un chemin de fichier Markdown en URL Docusaurus.

    - EN: website/docs/core/installation.md -> /whoosh-ng/core/installation
    - FR: website/i18n/fr/.../core/installation.md -> /whoosh-ng/fr/core/installation
    """
    content = doc_path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\\n(.*?)\\n---\\n", content, re.DOTALL)
    slug = None
    if fm_match:
        fm = fm_match.group(1)
        slug_match = re.search(r"^slug:\\s*(.*)$", fm, re.MULTILINE)
        if slug_match:
            slug = slug_match.group(1).strip()

    if slug:
        slug_path = slug.strip("/")
        if not slug_path:
            return f"{BASE_URL}/" if locale == "en" else f"{BASE_URL}/{locale}/"
        return f"{BASE_URL}/{slug_path}" if locale == "en" else f"{BASE_URL}/{locale}/{slug_path}"

    # Fallback: derive from file path
    if locale == "en":
        rel = doc_path.relative_to(DOCS_DIR)
    else:
        rel = doc_path.relative_to(DOCS_FR_DIR)
    rel_posix = rel.with_suffix("").as_posix()
    return f"{BASE_URL}/{locale}/{rel_posix}/"


def _title_from_path(md_file: Path) -> str:
    """Extrait un titre lisible a partir du nom de fichier."""
    return md_file.stem.replace("-", " ").replace("_", " ").title()


def generate() -> None:
    """Genere ``llms.txt`` (index) et ``llms-full.txt`` (corpus complet)."""
    full_md: list[str] = ["# whoosh-ng : Full Technical Documentation\\n"]
    index_md: list[str] = [
        "# whoosh-ng\\n",
        "> Documentation technique complete pour whoosh-ng.\\n",
        "## Core Documentation\\n",
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
            full_md.append(f"\\n\\n## DOCUMENT: {title}\\n")
            full_md.append(clean_content)

    # --- FR Markdown ---
    index_md.append("\\n## Documentation Française\\n")
    if DOCS_FR_DIR.exists():
        for md_file in sorted(DOCS_FR_DIR.rglob("*.md")):
            if md_file.name == "index.md":
                continue
            content = md_file.read_text(encoding="utf-8")
            clean_content = clean_front_matter(content)
            title = _title_from_path(md_file)
            url = _doc_url(md_file, "fr")
            index_md.append(f"- [{title}]({url})")
            full_md.append(f"\\n\\n## DOCUMENT (FR): {title}\\n")
            full_md.append(clean_content)

    # --- Code Examples ---
    index_md.append("\\n## Code Examples & Recipes\\n")
    full_md.append("\\n\\n# Code Examples\\n")
    if EXAMPLES_DIR.exists():
        for py_file in sorted(EXAMPLES_DIR.glob("*.py")):
            code = py_file.read_text(encoding="utf-8")
            full_md.append(f"\\n### Example: {py_file.name}\\n")
            full_md.append(f"```python\\n{code}\\n```")
            github_url = f"https://github.com/dorel14/whoosh-ng/blob/master/docs/archive_jekyll/_en/examples/{py_file.name}"
            index_md.append(f"- [Example: {py_file.name}]({github_url})")

    OUTPUT_INDEX.write_text("\\n".join(index_md), encoding="utf-8")
    OUTPUT_FULL.write_text("\\n".join(full_md), encoding="utf-8")
    # Also copy to static/ for Docusaurus to serve
    OUTPUT_INDEX_STATIC.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_INDEX_STATIC.write_text("\\n".join(index_md), encoding="utf-8")
    OUTPUT_FULL_STATIC.write_text("\\n".join(full_md), encoding="utf-8")
    print(f"Fichiers {OUTPUT_INDEX} et {OUTPUT_FULL} generes avec succes.")


if __name__ == "__main__":
    generate()
'''
    )
    script_path.write_text(new_script, encoding="utf-8")
    print("Lot D: scripts/generate_llm_docs.py updated")


# ─── Lot E: GitHub Actions ─────────────────────────────────────────────────────


def update_workflows() -> None:
    workflow = """name: Deploy GitHub Pages

# Build and deploy the Docusaurus site (source: website/) on every push to master
on:
  push:
    branches:
      - master
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    name: Build
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
          cache-dependency-path: website/package-lock.json

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install pydoctor
        run: pip install pydoctor

      - name: Generate changelog from GitHub releases
        run: python scripts/generate_changelog.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Generate API docs
        run: python scripts/generate_api_docs.py

      - name: Generate llms.txt
        run: python scripts/generate_llm_docs.py

      - name: Install dependencies
        working-directory: ./website
        run: npm ci

      - name: Build
        working-directory: ./website
        run: npm run build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./website/build
          include-hidden-files: true

  deploy:
    name: Deploy
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
"""
    (REPO_ROOT / ".github" / "workflows" / "pages.yml").write_text(workflow, encoding="utf-8")

    # llms-doc.yml — also trigger on website/ changes
    llms_path = REPO_ROOT / ".github" / "workflows" / "llms-doc.yml"
    llms = llms_path.read_text(encoding="utf-8")
    if "website/docs/**" not in llms:
        llms = llms.replace(
            "      - 'docs/**'",
            "      - 'docs/**'\n      - 'website/docs/**'\n      - 'website/i18n/**'",
        )
    llms_path.write_text(llms, encoding="utf-8")
    print("Lot E: pages.yml replaced, llms-doc.yml updated")


# ─── Rename intro.md -> index.md ────────────────────────────────────────────────


def _rename_intro_to_index() -> None:
    """Rename intro.md to index.md so Docusaurus serves it as the homepage.

    In Jekyll, the homepage was the file with permalink: /en/ or /fr/.
    In Docusaurus with routeBasePath: '/', index.md at the docs root
    becomes the homepage at /.
    """
    en_intro = WEBSITE_DIR / "docs" / "intro.md"
    en_index = WEBSITE_DIR / "docs" / "index.md"
    if en_intro.exists():
        en_intro.rename(en_index)

    fr_i18n = WEBSITE_DIR / "i18n" / "fr" / "docusaurus-plugin-content-docs" / "current"
    fr_intro = fr_i18n / "intro.md"
    fr_index = fr_i18n / "index.md"
    if fr_intro.exists():
        fr_intro.rename(fr_index)
    print("Renamed intro.md -> index.md (homepage)")


# ─── .gitignore ─────────────────────────────────────────────────────────────────


def update_gitignore() -> None:
    gitignore = REPO_ROOT / ".gitignore"

    # ─── Main ─────────────────────────────────────────────────────────────────────
    content = gitignore.read_text(encoding="utf-8")
    additions = []
    if "website/build/" not in content:
        additions.append("\n# Docusaurus build output\nwebsite/build/")
    if "website/node_modules/" not in content:
        additions.append("website/node_modules/")
    if additions:
        content += "\n".join(additions) + "\n"
        gitignore.write_text(content, encoding="utf-8")
        print(".gitignore: added Docusaurus entries")


# ─── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    print("=" * 60)
    print("Jekyll -> Docusaurus Migration")
    print("=" * 60)

    create_website_scaffold()
    migrate_en()
    migrate_fr()

    # Rename intro.md to index.md for both locales (homepage)
    _rename_intro_to_index()

    (WEBSITE_DIR / "sidebars.ts").write_text(EN_SIDEBAR, encoding="utf-8")

    update_llm_docs_script()
    update_workflows()
    update_gitignore()

    print("=" * 60)
    print("Migration complete!")
    print(f"  Site: {WEBSITE_DIR}")
    print("  Build: cd website && npm ci && npm run build")
    print("=" * 60)


if __name__ == "__main__":
    main()
