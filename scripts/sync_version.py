from __future__ import annotations

import re
import sys
import tomllib
from datetime import UTC, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
INIT_PY = ROOT / "src" / "whoosh" / "__init__.py"
README_MD = ROOT / "README.md"
CONFIG_YML = ROOT / "docs" / "archive_jekyll" / "_config.yml"
INDEX_EN = ROOT / "docs" / "archive_jekyll" / "_en" / "index.md"
INDEX_FR = ROOT / "docs" / "archive_jekyll" / "_fr" / "index.md"

# Docusaurus paths
DOCS_DIR = ROOT / "website" / "docs"
DOCS_FR_DIR = ROOT / "website" / "i18n" / "fr" / "docusaurus-plugin-content-docs" / "current"
DOCUSAURUS_CONFIG_TS = ROOT / "website" / "docusaurus.config.ts"


def get_version_from_pyproject() -> str:
    with PYPROJECT.open("rb") as f:
        data = tomllib.load(f)
    version: str = data["project"]["version"]
    return version


def update_init_py(version: str) -> bool:
    """Update __version__ tuple and __version_string__ in src/whoosh/__init__.py."""
    content = INIT_PY.read_text()

    parts = [int(p) for p in version.split(".")]
    tuple_repr = "(" + ", ".join(str(p) for p in parts) + ")"

    new_content = re.sub(
        r"__version__ = \([^)]+\)",
        f"__version__ = {tuple_repr}",
        content,
    )

    new_content = re.sub(
        r'__version_string__ = "[^"]*"',
        f'__version_string__ = "{version}"',
        new_content,
    )

    if new_content != content:
        INIT_PY.write_text(new_content)
        return True
    return False


def update_readme(version: str) -> bool:
    """Update version references in README.md."""
    content = README_MD.read_text()

    new_content = re.sub(
        r"Version \d+\.\d+\.\d+ brings",
        f"Version {version} brings",
        content,
    )

    new_content = re.sub(
        r"## Recent Changes in \d+\.\d+\.\d+",
        f"## Recent Changes in {version}",
        new_content,
    )

    if new_content != content:
        README_MD.write_text(new_content)
        return True
    return False


def update_docs_config_yml(version: str) -> bool:
    """Update the footer version and date in docs/_config.yml (Jekyll legacy)."""
    config_yml = REPO_ROOT / "docs" / "archive_jekyll" / "_config.yml"
    if not config_yml.exists():
        return False
    content = config_yml.read_text()
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    new_content = re.sub(
        r'footer_content: "Whoosh-NG Documentation [^\"]*"',
        f'footer_content: "Whoosh-NG Documentation v{version} | Last updated: {today}"',
        content,
    )

    if new_content != content:
        config_yml.write_text(new_content)
        return True
    return False


def update_docusaurus_config(version: str) -> bool:
    """Update the copyright footer version in website/docusaurus.config.ts."""
    if not DOCUSAURUS_CONFIG_TS.exists():
        return False
    content = DOCUSAURUS_CONFIG_TS.read_text(encoding="utf-8")
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    new_content = re.sub(
        r"copyright: 'Whoosh-NG Documentation v[\d.]+ \| Last updated: [\d-]+'",
        f"copyright: 'Whoosh-NG Documentation v{version} | Last updated: {today}'",
        content,
    )

    if new_content != content:
        DOCUSAURUS_CONFIG_TS.write_text(new_content, encoding="utf-8")
        return True
    return False


def update_docs_index_en(version: str) -> bool:
    """Update version reference in docs/_en/index.md."""
    if not INDEX_EN.exists():
        return False
    content = INDEX_EN.read_text()
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    new_content = re.sub(
        r"> \*\*Latest release\*\*: v[\d.]+.*\n",
        (
            f"> **Latest release**: v{version} | "
            "[View releases on GitHub](https://github.com/dorel14/whoosh-ng/releases) | "
            f"Next: v4.0.0.dev0 (in development) | Last updated: {today}\n"
        ),
        content,
    )

    if new_content != content:
        INDEX_EN.write_text(new_content)
        return True
    return False


def update_docs_index_fr(version: str) -> bool:
    """Update version reference in docs/_fr/index.md (Jekyll legacy)."""
    if not INDEX_FR.exists():
        return False
    content = INDEX_FR.read_text()
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    new_content = re.sub(
        r"> \*\*Dernière version publiée\*\*: v[\d.]+.*\n",
        (
            f"> **Dernière version publiée**: v{version} | "
            "[Voir les releases sur GitHub](https://github.com/dorel14/whoosh-ng/releases) | "
            "Prochaine: v4.0.0.dev0 (en développement)\n"
        ),
        content,
    )

    if new_content != content:
        INDEX_FR.write_text(new_content)
        return True
    return False


def update_docusaurus_index_en(version: str) -> bool:
    """Update version reference in website/docs/index.md."""
    doc = DOCS_DIR / "index.md"
    if not doc.exists():
        return False
    content = doc.read_text(encoding="utf-8")
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    new_content = re.sub(
        r"Latest release\*\*: v[\d.]+.*\n",
        f"Latest release**: v{version} | "
        "[View releases on GitHub](https://github.com/dorel14/whoosh-ng/releases) | "
        f"Next: v4.0.0.dev0 (in development) | Last updated: {today}\n",
        content,
    )

    if new_content != content:
        doc.write_text(new_content, encoding="utf-8")
        return True
    return False


def update_docusaurus_index_fr(version: str) -> bool:
    """Update version reference in website/i18n/fr/.../index.md."""
    doc = DOCS_FR_DIR / "index.md"
    if not doc.exists():
        return False
    content = doc.read_text(encoding="utf-8")
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    new_content = re.sub(
        r"Dernière version publiée\*\*: v[\d.]+.*\n",
        f"Derniere version publiee**: v{version} | "
        "[Voir les releases sur GitHub](https://github.com/dorel14/whoosh-ng/releases) | "
        f"Prochaine: v4.0.0.dev0 (en développement)\n",
        content,
    )

    if new_content != content:
        doc.write_text(new_content, encoding="utf-8")
        return True
    return False


def update_plugin_versions(version: str) -> bool:
    """Update version strings in built-in plugin classes."""
    changed = False
    plugin_files = [
        ROOT / "src" / "whoosh_modern" / "autocomplete" / "plugin.py",
        ROOT / "src" / "whoosh_modern" / "vector" / "plugin.py",
    ]
    for pf in plugin_files:
        if not pf.exists():
            continue
        content = pf.read_text()
        new_content = re.sub(
            r'version = "[\d.]+"(\s*$)',
            f'version = "{version}"\\1',
            content,
            flags=re.MULTILINE,
        )
        if new_content != content:
            pf.write_text(new_content)
            changed = True

    # whoosh_fastapi and whoosh_admin use FastAPI version= in create_app
    fastapi_init = ROOT / "src" / "whoosh_fastapi" / "__init__.py"
    if fastapi_init.exists():
        content = fastapi_init.read_text()
        new_content = re.sub(
            r'version="[\d.]+"',
            f'version="{version}"',
            content,
        )
        if new_content != content:
            fastapi_init.write_text(new_content)
            changed = True

    admin_init = ROOT / "src" / "whoosh_admin" / "__init__.py"
    if admin_init.exists():
        content = admin_init.read_text()
        new_content = re.sub(
            r'version="[\d.]+"',
            f'version="{version}"',
            content,
        )
        if new_content != content:
            admin_init.write_text(new_content)
            changed = True

    return changed


def update_docusaurus_package_json(version: str) -> bool:
    """Update the version field in website/package.json."""
    pkg = ROOT / "website" / "package.json"
    if not pkg.exists():
        return False
    content = pkg.read_text(encoding="utf-8")

    new_content = re.sub(
        r'  "version": "[^"]*"',
        f'  "version": "{version}"',
        content,
    )

    if new_content != content:
        pkg.write_text(new_content, encoding="utf-8")
        return True
    return False


def main() -> int:
    version = get_version_from_pyproject()
    changed = False

    if update_init_py(version):
        print(f"  Updated {INIT_PY.relative_to(ROOT)}")
        changed = True

    if update_readme(version):
        print(f"  Updated {README_MD.relative_to(ROOT)}")
        changed = True

    if update_docs_config_yml(version):
        print(f"  Updated {CONFIG_YML.relative_to(ROOT)}")
        changed = True

    if update_docs_index_en(version):
        print(f"  Updated {INDEX_EN.relative_to(ROOT)}")
        changed = True

    if update_docs_index_fr(version):
        print(f"  Updated {INDEX_FR.relative_to(ROOT)}")
        changed = True

    if update_docusaurus_config(version):
        print(f"  Updated {DOCUSAURUS_CONFIG_TS.relative_to(ROOT)}")
        changed = True

    if update_docusaurus_index_en(version):
        print(f"  Updated {DOCS_DIR / 'index.md'}")
        changed = True

    if update_docusaurus_index_fr(version):
        print(f"  Updated {DOCS_FR_DIR / 'index.md'}")
        changed = True

    if update_docusaurus_package_json(version):
        print(f"  Updated {ROOT / 'website' / 'package.json'}")
        changed = True

    if update_plugin_versions(version):
        print("  Updated plugin version attributes")
        changed = True

    # Regenerate changelog from GitHub releases
    try:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_changelog.py")],
            check=False,
            env={**__import__("os").environ, "GITHUB_TOKEN": get_github_token() or ""},
        )
        print("  Regenerated changelog from GitHub releases")
        changed = True
    except Exception as e:
        print(f"  Changelog generation skipped: {e}", file=sys.stderr)

    if changed:
        print(f"Version synchronized to {version}")
    else:
        print(f"Version {version} is already in sync")

    return 0


if __name__ == "__main__":
    sys.exit(main())
