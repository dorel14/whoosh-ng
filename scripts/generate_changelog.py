"""Module de generation automatique du changelog a partir des releases et commits GitHub.

Ce module interroge l'API GitHub pour recuperer les releases publiques
et les messages de commits associes, puis genere un fichier markdown
``core/changelog.md`` dans la documentation Docusaurus. Chaque release
devient une section avec son titre, sa date, sa description et la liste
des commits (avec categories Conventional Commits).

Le script peut etre declenche manuellement ou via une Action GitHub
apres chaque publication de release.

Auteur: SoniqueBay Team
Version: 1.1.0
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_EN_DIR = REPO_ROOT / "website" / "docs"
DOCS_FR_DIR = REPO_ROOT / "website" / "i18n" / "fr" / "docusaurus-plugin-content-docs" / "current"

GITHUB_REPO = "dorel14/whoosh-ng"
GITHUB_API = "https://api.github.com/repos/{repo}/releases"
GITHUB_COMMITS_API = "https://api.github.com/repos/{repo}/compare/{{prev}}...{{curr}}"

# Conventional Commit types for categorization
COMMIT_TYPES = {
    "feat": ("Features", "Fonctionnalités"),
    "fix": ("Bug Fixes", "Corrections de bugs"),
    "perf": ("Performance Improvements", "Améliorations de performance"),
    "refactor": ("Code Refactoring", "Refactorisation"),
    "docs": ("Documentation", "Documentation"),
    "test": ("Tests", "Tests"),
    "chore": ("Chores", "Tâches diverses"),
    "ci": ("CI/CD", "CI/CD"),
    "build": ("Build System", "Système de build"),
}


def get_github_token() -> str | None:
    """Retrieve the GitHub token from environment or git config.

    Returns:
        The GitHub token string, or None if not found.
    """
    import os

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token

    try:
        result = subprocess.run(
            ["git", "config", "--get", "github.token"],
            capture_output=True,
            text=True,
            check=False,
        )
        token = result.stdout.strip()
        if token:
            return token
    except Exception:
        pass

    return None


def _api_request(url: str, token: str | None = None) -> dict | list | None:
    """Make a GET request to the GitHub API.

    Args:
        url: The full API URL to request.
        token: Optional GitHub token for authentication.

    Returns:
        Parsed JSON response, or None on error.
    """
    import urllib.request

    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"API request error for {url}: {e}", file=sys.stderr)
        return None


def fetch_releases(token: str | None = None, per_page: int = 30) -> list[dict]:
    """Fetch the latest releases from GitHub API.

    Args:
        token: Optional GitHub token for authentication.
        per_page: Number of releases to fetch (max 100).

    Returns:
        List of release dicts, most recent first.
    """
    url = GITHUB_API.format(repo=GITHUB_REPO) + f"?per_page={per_page}"
    data = _api_request(url, token)
    return data if isinstance(data, list) else []


def fetch_commits_between(prev_tag: str, curr_tag: str, token: str | None = None) -> list[dict]:
    """Fetch commits between two Git tags using the GitHub compare API.

    Args:
        prev_tag: The previous release tag (e.g. 'v4.0.0').
        curr_tag: The current release tag (e.g. 'v4.0.1').
        token: Optional GitHub token for authentication.

    Returns:
        List of commit dicts from the compare response.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/compare/{prev_tag}...{curr_tag}"
    data = _api_request(url, token)
    if data and isinstance(data, dict) and "commits" in data:
        return data["commits"]
    return []


def categorize_commit(message: str, locale: str = "en") -> tuple[str, str]:
    """Categorize a commit message using Conventional Commits.

    Args:
        message: The full commit message.
        locale: 'en' or 'fr' for category label.

    Returns:
        Tuple of (category_key, commit_summary).
    """
    first_line = message.split("\n")[0].strip()
    # Match conventional commit format: type(scope): description
    m = re.match(r"^(\w+)(?:\([^)]+\))?:\s*(.+)$", first_line)
    if m:
        ctype = m.group(1).lower()
        summary = m.group(2).strip()
        if ctype in COMMIT_TYPES:
            label = COMMIT_TYPES[ctype][1 if locale == "fr" else 0]
            return (label, summary)
    return ("Other" if locale == "en" else "Autre", first_line)


def format_commit_list(commits: list[dict], locale: str = "en") -> str:
    """Format a list of commits into categorized markdown sections.

    Args:
        commits: List of commit dicts from the GitHub API.
        locale: 'en' or 'fr'.

    Returns:
        Markdown string with categorized commits.
    """
    if not commits:
        return "_No commits found._"

    # Categorize commits
    categories: dict[str, list[str]] = {}
    for commit in commits:
        msg = commit.get("commit", {}).get("message", "")
        sha = commit.get("sha", "")[:7]
        cat_key, summary = categorize_commit(msg, locale)
        if not summary:
            continue
        categories.setdefault(cat_key, []).append(summary)

    if not categories:
        return "_No release-worthy commits found._"

    lines = []
    for cat, summaries in categories.items():
        lines.append(f"### {cat}")
        lines.append("")
        for s in summaries:
            lines.append(f"- {s}")
        lines.append("")

    return "\n".join(lines)


def format_release_notes(release: dict, all_releases: list[dict], token: str | None = None) -> str:
    """Format a single release's notes as markdown, including commit messages.

    Args:
        release: The release dict from GitHub API.
        all_releases: All releases (to find the previous tag).
        token: Optional GitHub token for fetching commits.

    Returns:
        Markdown string for the release section.
    """
    tag = release.get("tag_name", "unknown")
    name = release.get("name") or tag
    body = release.get("body", "") or ""
    published = release.get("published_at", "")

    if published:
        date = datetime.fromisoformat(published.replace("Z", "+00:00"))
        date_str = date.strftime("%Y-%m-%d")
    else:
        date_str = "unreleased"

    version = re.sub(r"^v", "", tag)

    # Find previous tag for commit comparison
    try:
        idx = all_releases.index(release)
    except ValueError:
        idx = -1
    prev_tag = (
        all_releases[idx + 1].get("tag_name") if idx >= 0 and idx + 1 < len(all_releases) else None
    )

    lines = [
        f"## {name} ({date_str})",
        f"**Tag**: `{tag}`",
        "",
    ]

    # Body (release notes from GitHub)
    if body.strip():
        lines.append(body.strip())
        lines.append("")

    # Commit messages
    if prev_tag:
        commits = fetch_commits_between(prev_tag, tag, token)
        if commits:
            commit_section = format_commit_list(commits, locale="en")
            if commit_section:
                lines.append("### Commits")
                lines.append("")
                lines.append(commit_section)

    lines.append("")
    lines.append(f"[View on GitHub](https://github.com/{GITHUB_REPO}/releases/tag/{tag})")
    lines.append("")

    return "\n".join(lines)


def generate_changelog(locale: str = "en", token: str | None = None) -> str:
    """Generate the full changelog markdown content.

    Args:
        locale: 'en' or 'fr' — used for the heading text.
        token: Optional GitHub token for API rate limiting.
    """
    releases = fetch_releases(token)

    if locale == "en":
        title = "Changelog"
        intro = (
            "Release notes for Whoosh-NG, auto-generated from GitHub releases and commit messages."
        )
    else:
        title = "Historique des modifications"
        intro = (
            "Notes de version pour Whoosh-NG, generees automatiquement "
            "a partir des releases GitHub et des messages de commits."
        )

    lines = [
        "---",
        f'title: "{title}"',
        "sidebar_position: 80",
        "sidebars: changelogSidebar",
        "---",
        "",
        f"# {title}",
        "",
        intro,
        "",
    ]

    if not releases:
        lines.append("_No releases published yet._")
        lines.append("")
    else:
        for i, release in enumerate(releases):
            if release.get("prerelease", False) and i >= 10:
                continue
            lines.append(format_release_notes(release, releases, token))

    return "\n".join(lines)


def generate() -> None:
    """Generate changelog docs for both EN and FR locales."""
    token = get_github_token()

    en_content = generate_changelog("en", token)
    fr_content = generate_changelog("fr", token)

    en_path = DOCS_EN_DIR / "core" / "changelog.md"
    fr_path = DOCS_FR_DIR / "core" / "changelog.md"

    en_path.parent.mkdir(parents=True, exist_ok=True)
    fr_path.parent.mkdir(parents=True, exist_ok=True)

    en_path.write_text(en_content, encoding="utf-8")
    print(f"Generated: {en_path}")

    fr_path.write_text(fr_content, encoding="utf-8")
    print(f"Generated: {fr_path}")


if __name__ == "__main__":
    generate()
