from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
INIT_PY = ROOT / "src" / "whoosh" / "__init__.py"
README_MD = ROOT / "README.md"


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


def main() -> int:
    version = get_version_from_pyproject()
    changed = False

    if update_init_py(version):
        print(f"  Updated {INIT_PY.relative_to(ROOT)}")
        changed = True

    if update_readme(version):
        print(f"  Updated {README_MD.relative_to(ROOT)}")
        changed = True

    if changed:
        print(f"Version synchronized to {version}")
    else:
        print(f"Version {version} is already in sync")

    return 0


if __name__ == "__main__":
    sys.exit(main())
