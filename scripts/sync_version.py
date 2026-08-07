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
CONFIG_YML = ROOT / "docs" / "_config.yml"
INDEX_EN = ROOT / "docs" / "_en" / "index.md"
INDEX_FR = ROOT / "docs" / "_fr" / "index.md"


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


def update_docs_config(version: str) -> bool:
    """Update the footer version and date in docs/_config.yml."""
    content = CONFIG_YML.read_text()
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    new_content = re.sub(
        r"footer_content: \"Whoosh-NG Documentation [^\"]*\"",
        f'footer_content: "Whoosh-NG Documentation v{version} | Last updated: {today}"',
        content,
    )

    if new_content != content:
        CONFIG_YML.write_text(new_content)
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
    """Update version reference in docs/_fr/index.md."""
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


def main() -> int:
    version = get_version_from_pyproject()
    changed = False

    if update_init_py(version):
        print(f"  Updated {INIT_PY.relative_to(ROOT)}")
        changed = True

    if update_readme(version):
        print(f"  Updated {README_MD.relative_to(ROOT)}")
        changed = True

    if update_docs_config(version):
        print(f"  Updated {CONFIG_YML.relative_to(ROOT)}")
        changed = True

    if update_docs_index_en(version):
        print(f"  Updated {INDEX_EN.relative_to(ROOT)}")
        changed = True

    if update_docs_index_fr(version):
        print(f"  Updated {INDEX_FR.relative_to(ROOT)}")
        changed = True

    if update_plugin_versions(version):
        print("  Updated plugin version attributes")
        changed = True

    if changed:
        print(f"Version synchronized to {version}")
    else:
        print(f"Version {version} is already in sync")

    return 0


if __name__ == "__main__":
    sys.exit(main())
