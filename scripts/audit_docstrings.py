"""Audit docstrings in the Whoosh-NG codebase for Google-style compliance.

Scans all Python files in src/ and reports:
- Files with Google-style docstrings (Args:, Returns:, Raises:, Yields:, Note:, Example:)
- Files without any docstrings
- Files with non-Google-style docstrings (e.g. reST-style with :param:, :return:)
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIRS = [
    REPO_ROOT / "src" / "whoosh",
    REPO_ROOT / "src" / "whoosh_modern",
    REPO_ROOT / "src" / "whoosh_fastapi",
    REPO_ROOT / "src" / "whoosh_admin",
]

GOOGLE_PATTERNS = re.compile(
    r"^\s+(Args|Returns|Raises|Yields|Note|Example|Attributes|See Also):",
    re.MULTILINE,
)
REST_PATTERNS = re.compile(
    r"^\s+:(param|return|returns|raises|type|rtype|ivar|vartype|cvar):", re.MULTILINE
)
DOCSTRING_START = re.compile(r'^\s*"""')


def audit_file(path: Path) -> dict:
    """Audit a single Python file for docstring style.

    Args:
        path: Path to the Python file.

    Returns:
        Dict with keys: has_docstring, google_count, rest_count, module_docstring.
    """
    content = path.read_text(encoding="utf-8")

    # Count Google-style and reST-style docstring markers
    google = len(GOOGLE_PATTERNS.findall(content))
    rest = len(REST_PATTERNS.findall(content))

    # Check for any docstring at all
    has_docstring = '"""' in content or "'''" in content

    return {
        "has_docstring": has_docstring,
        "google_count": google,
        "rest_count": rest,
    }


def main() -> None:
    """Run the docstring audit."""
    results = {"total": 0, "no_doc": 0, "google_only": 0, "rest_only": 0, "mixed": 0, "no_style": 0}
    files_with_rest = []

    for src_dir in SRC_DIRS:
        if not src_dir.exists():
            continue
        for py in sorted(src_dir.rglob("*.py")):
            is_internal = py.name.startswith("_") and py.suffix == ".py"
            if is_internal and not py.parent.name.startswith("test"):
                pass  # Skip internal files but still count them
            info = audit_file(py)
            results["total"] += 1

            if not info["has_docstring"]:
                results["no_doc"] += 1
                continue

            if info["google_count"] > 0 and info["rest_count"] == 0:
                results["google_only"] += 1
            elif info["rest_count"] > 0 and info["google_count"] == 0:
                results["rest_only"] += 1
                files_with_rest.append(py.relative_to(REPO_ROOT))
            elif info["google_count"] > 0 and info["rest_count"] > 0:
                results["mixed"] += 1
                files_with_rest.append(py.relative_to(REPO_ROOT))
            else:
                results["no_style"] += 1

    print("=== Docstring Audit ===")
    print(f"Total Python files: {results['total']}")
    print(f"  With Google-style docstrings: {results['google_only']}")
    print(f"  With reST-style docstrings:    {results['rest_only']}")
    print(f"  Mixed style:                   {results['mixed']}")
    print(f"  With docstrings, no style:     {results['no_style']}")
    print(f"  No docstrings at all:          {results['no_doc']}")

    if files_with_rest:
        print("\nFiles with reST-style or mixed docstrings (need updating to Google style):")
        for f in files_with_rest[:50]:
            print(f"  {f}")
        if len(files_with_rest) > 50:
            print(f"  ... and {len(files_with_rest) - 50} more")


if __name__ == "__main__":
    main()
