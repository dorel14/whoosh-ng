#!/usr/bin/env python3
"""Sync Whoosh-NG roadmap.md vers GitHub Project v2 — version idempotente.

Champs du Project:
- Status: SELECT (Done / In Progress / Planned / Deferred)
- Epic: TEXT (ex. "EPIC 4.5", "Sprint G")
- Priority: SELECT (High / Medium / Low)

Corrections appliquees:
- Idempotence : matcher par titre, update si existe, create sinon.
- Peuplement complet : Status + Epic (texte) + Priority.
- Aucun draft issue : tout est une vraie issue GitHub.
  - Epic → issue GitHub réelle, ajoutée au Project.
  - Sprint → issue GitHub réelle, ajoutée au Project.
    (Sub-issues activable plus tard via `gh issue create -- --parent N`
    quand la feature sera activée dans les settings du repo.)
- Lots → créés comme milestones GitHub, les issues correspondantes sont taguées.
- Utilise gh CLI pour l'authentification et l'API REST Projects v2.

Usage:
    gh auth login --scopes "project repo"
    python scripts/sync_roadmap_to_project.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import Any, cast

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO = "dorel14/whoosh-ng"
PROJECT_NUMBER = 2
ROADMAP_PATH = ".kilo/plans/1786003980063-whoosh-ng-roadmap.md"
OWNER = "dorel14"

EMOJI_TO_STATUS = {
    "✅": "Done",
    "🟡": "In Progress",
    "🔴": "Planned",
    "⏸️": "Deferred",
    "🟢": "Done",
}

PRIORITY_FROM_STATUS = {
    "Done": "High",
    "In Progress": "High",
    "Planned": "Medium",
    "Deferred": "Low",
    "Blocked": "Medium",
}

STATUS_KEYWORDS = {
    "DONE": "Done",
    "IN_PROGRESS": "In Progress",
    "PLANNED": "Planned",
    "DEFERRED": "Deferred",
    "BLOCKED": "Blocked",
    "PARTIEL": "In Progress",
    "TODO": "Planned",
    "REPORTÉ": "Deferred",
    "REPORTÉE": "Deferred",
    "ANNULÉ": "Deferred",
    "ANNULÉE": "Deferred",
    "À FAIRE": "Planned",
}


def status_from_text(text: str) -> str | None:
    """Extrait le status (Done/In Progress/Planned/Deferred/Blocked) depuis un texte."""
    for emoji, mapped in EMOJI_TO_STATUS.items():
        if emoji in text:
            return mapped
    upper = text.upper()
    for keyword, mapped in STATUS_KEYWORDS.items():
        if keyword in upper:
            return mapped
    return None


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------


def get_gh_token() -> str:
    """Récupère le token depuis gh CLI."""
    result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
    return result.stdout.strip()


session = requests.Session()
retry_strategy = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS", "TRACE"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

GH_TOKEN = get_gh_token()
GH_HEADERS = {
    "Authorization": f"token {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
GRAPHQL_HEADERS = {
    **GH_HEADERS,
    "GraphQL-Features": "issue_types,sub_issues",
}


def gh_get(path: str, params: dict[str, Any] | None = None) -> Any:
    resp = session.get(
        f"https://api.github.com{path}",
        headers=GH_HEADERS,
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def gh_post(path: str, body: dict[str, Any]) -> Any:
    resp = session.post(
        f"https://api.github.com{path}",
        headers=GH_HEADERS,
        json=body,
        timeout=30,
    )
    if resp.status_code == 429:
        import time

        reset = int(resp.headers.get("X-RateLimit-Reset", 0))
        sleep = max(reset - time.time(), 1)
        print(f"⏳ Rate limit, pause {sleep:.1f}s")
        time.sleep(sleep)
        return gh_post(path, body)
    resp.raise_for_status()
    return resp.json()


def gh_patch(path: str, body: dict[str, Any]) -> Any:
    resp = session.patch(
        f"https://api.github.com{path}",
        headers=GH_HEADERS,
        json=body,
        timeout=30,
    )
    if resp.status_code == 429:
        import time

        reset = int(resp.headers.get("X-RateLimit-Reset", 0))
        sleep = max(reset - time.time(), 1)
        print(f"⏳ Rate limit, pause {sleep:.1f}s")
        time.sleep(sleep)
        return gh_patch(path, body)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Project helpers
# ---------------------------------------------------------------------------


def get_project_node_id() -> str:
    query = """
    query($owner: String!, $number: Int!) {
      user(login: $owner) {
        projectV2(number: $number) { id }
      }
    }
    """
    payload: dict[str, Any] = {
        "query": query,
        "variables": {"owner": OWNER, "number": PROJECT_NUMBER},
    }
    resp = session.post(
        "https://api.github.com/graphql",
        json=payload,
        headers=GRAPHQL_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return cast(str, data["data"]["user"]["projectV2"]["id"])


def gh_graphql(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables
    resp = session.post(
        "https://api.github.com/graphql",
        json=payload,
        headers=GRAPHQL_HEADERS,
        timeout=30,
    )
    if resp.status_code == 429:
        import time

        reset = int(resp.headers.get("X-RateLimit-Reset", 0))
        sleep = max(reset - time.time(), 1)
        print(f"⏳ Rate limit, pause {sleep:.1f}s")
        time.sleep(sleep)
        return gh_graphql(query, variables)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return cast(dict[str, Any], data.get("data") or {})


def get_fields(project_id: str) -> dict[str, dict[str, Any]]:
    query = """
    query($project_id: ID!) {
      node(id: $project_id) {
        ... on ProjectV2 {
          fields(first: 50) {
            nodes {
              ... on ProjectV2Field { id name }
              ... on ProjectV2SingleSelectField { id name options { id name } }
            }
          }
        }
      }
    }
    """
    payload: dict[str, Any] = {
        "query": query,
        "variables": {"project_id": project_id},
    }
    resp = session.post(
        "https://api.github.com/graphql",
        json=payload,
        headers=GRAPHQL_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    fields: dict[str, dict[str, Any]] = {}
    for f in cast(list[dict[str, Any]], data["data"]["node"]["fields"]["nodes"]):
        field_name = cast(str, f.get("name", ""))
        if not field_name:
            continue
        field_type = "SELECT" if "options" in f else "TEXT"
        fields[field_name] = {"id": cast(str, f["id"]), "type": field_type, **f}
    return fields


def get_existing_items(project_id: str) -> dict[str, str]:
    """Récupère les items existants via l'API REST."""
    items: dict[str, str] = {}
    page = 1
    while True:
        data = gh_get(
            f"/users/{OWNER}/projectsV2/{PROJECT_NUMBER}/items",
            {"per_page": 100, "page": page},
        )
        if not data:
            break
        for item in data:
            item_id = str(item.get("id", ""))
            node_id = str(item.get("node_id", ""))
            content = item.get("content")
            if content and content.get("title"):
                items[cast(str, content["title"])] = node_id
            else:
                field_values = item.get("fields", [])
                for fv in field_values:
                    if fv.get("name") == "Title" and fv.get("value"):
                        items[cast(str, fv["value"])] = node_id
                        break
        if len(data) < 100:
            break
        page += 1
    return items


def get_or_create_item(project_id: str, title: str, cache: dict[str, str]) -> str:
    """FALLBACK: crée un draft issue dans le projet.

    Utilise uniquement si l'issue GitHub n'existe pas.
    """
    if title in cache:
        return cache[title]

    query = """
    mutation($project_id: ID!, $title: String!) {
      addProjectV2DraftIssue(input: {projectId: $project_id, title: $title}) {
        projectItem { id }
      }
    }
    """
    data = gh_graphql(query, {"project_id": project_id, "title": title})
    node_id = cast(str, data["addProjectV2DraftIssue"]["projectItem"]["id"])
    cache[title] = node_id
    return cache[title]


def set_field_value(item_id: str, field_id: str, value: dict[str, Any]) -> None:
    """Met à jour un champ d'un item projet via REST."""
    gh_patch(
        f"/projects/columns/cards/{item_id}",
        {"field_ids": [field_id], "project_id": item_id},
    )


def set_select_field(project_id: str, item_id: str, field_id: str, option_id: str) -> None:
    query = """
    mutation($input: UpdateProjectV2ItemFieldValueInput!) {
      updateProjectV2ItemFieldValue(input: $input) { projectV2Item { id } }
    }
    """
    gh_graphql(
        query,
        {
            "input": {
                "projectId": project_id,
                "itemId": item_id,
                "fieldId": field_id,
                "value": {"singleSelectOptionId": option_id},
            }
        },
    )


def set_text_field(project_id: str, item_id: str, field_id: str, value: str) -> None:
    query = """
    mutation($input: UpdateProjectV2ItemFieldValueInput!) {
      updateProjectV2ItemFieldValue(input: $input) { projectV2Item { id } }
    }
    """
    gh_graphql(
        query,
        {
            "input": {
                "projectId": project_id,
                "itemId": item_id,
                "fieldId": field_id,
                "value": {"text": value},
            }
        },
    )


# ---------------------------------------------------------------------------
# GitHub Issues helpers
# ---------------------------------------------------------------------------


def get_repo_node_id() -> str:
    query = """
    query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) { id }
    }
    """
    payload: dict[str, Any] = {
        "query": query,
        "variables": {"owner": OWNER, "repo": REPO.split("/")[1]},
    }
    resp = session.post(
        "https://api.github.com/graphql", json=payload, headers=GRAPHQL_HEADERS, timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return cast(str, data["data"]["repository"]["id"])


def get_issue_node_id(repo_id: str, issue_number: int) -> str:
    query = """
    query($repo_id: ID!, $number: Int!) {
      node(id: $repo_id) {
        ... on Repository {
          issue(number: $number) { id }
        }
      }
    }
    """
    payload: dict[str, Any] = {
        "query": query,
        "variables": {"repo_id": repo_id, "number": issue_number},
    }
    resp = session.post(
        "https://api.github.com/graphql", json=payload, headers=GRAPHQL_HEADERS, timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return cast(str, data["data"]["node"]["issue"]["id"])


def create_issue(repo_id: str, title: str, body: str) -> tuple[int, str]:
    """Crée une issue GraphQL et retourne (number, node_id)."""
    query = """
    mutation($input: CreateIssueInput!) {
      createIssue(input: $input) {
        issue { number id }
      }
    }
    """
    payload: dict[str, Any] = {
        "query": query,
        "variables": {
            "input": {
                "repositoryId": repo_id,
                "title": title,
                "body": body,
            }
        },
    }
    resp = session.post(
        "https://api.github.com/graphql",
        json=payload,
        headers=GRAPHQL_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    number = int(data["data"]["createIssue"]["issue"]["number"])
    node_id = cast(str, data["data"]["createIssue"]["issue"]["id"])
    return number, node_id


def add_sub_issue(parent_issue_number: int, child_issue_number: int) -> bool:
    """Lie une issue enfant comme sub-issue d'une issue parent via GraphQL mutation.

    Utilise le header GraphQL-Features: sub_issues pour activer la feature.
    """
    repo_id = get_repo_node_id()
    parent_id = get_issue_node_id(repo_id, parent_issue_number)
    child_id = get_issue_node_id(repo_id, child_issue_number)

    mutation = """
    mutation($parentIssueId: ID!, $childIssueId: ID!) {
      addSubIssue(input: { issueId: $parentIssueId, subIssueId: $childIssueId }) {
        issue { number }
        subIssue { number }
      }
    }
    """
    data = gh_graphql(
        mutation,
        {"parentIssueId": parent_id, "childIssueId": child_id},
    )
    return bool(data.get("addSubIssue"))


def is_sub_issue(parent_issue_number: int, child_issue_number: int) -> bool:
    """Vérifie si une issue est déjà une sub-issue d'une autre via GraphQL."""
    repo_id = get_repo_node_id()
    parent_id = get_issue_node_id(repo_id, parent_issue_number)
    child_id = get_issue_node_id(repo_id, child_issue_number)
    query = """
    query($parentId: ID!) {
      node(id: $parentId) {
        ... on Issue {
          subIssues(first: 100) {
            nodes { number }
          }
        }
      }
    }
    """
    data = gh_graphql(query, {"parentId": parent_id})
    sub_issues = data.get("node", {}).get("subIssues", {}).get("nodes", [])
    return any(s.get("number") == child_issue_number for s in sub_issues)


def add_issue_to_project(project_id: str, issue_node_id: str) -> str:
    query = """
    mutation($project_id: ID!, $content_id: ID!) {
      addProjectV2ItemById(input: {projectId: $project_id, contentId: $content_id}) {
        item { id }
      }
    }
    """
    payload: dict[str, Any] = {
        "query": query,
        "variables": {"project_id": project_id, "content_id": issue_node_id},
    }
    resp = session.post(
        "https://api.github.com/graphql",
        json=payload,
        headers=GRAPHQL_HEADERS,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return cast(str, data["data"]["addProjectV2ItemById"]["item"]["id"])


def get_or_create_milestone(title: str) -> int:
    """Crée ou récupère un milestone par titre. Retourne l'issue number du milestone (ID entier)."""
    path = f"/repos/{REPO}/milestones"
    data = gh_get(path, {"state": "all", "per_page": 100})
    for m in data:
        if m.get("title") == title:
            return int(m["number"])

    resp = session.post(
        f"https://api.github.com{path}",
        headers=GH_HEADERS,
        json={"title": title, "state": "open"},
        timeout=30,
    )
    resp.raise_for_status()
    return int(resp.json()["number"])


def set_issue_milestone(issue_number: int, milestone_number: int) -> None:
    """Tague une issue avec un milestone via REST PATCH."""
    gh_patch(
        f"/repos/{REPO}/issues/{issue_number}",
        {"milestone": milestone_number},
    )


# ---------------------------------------------------------------------------
# Roadmap file helpers
# ---------------------------------------------------------------------------

ISSUE_REF_RE = re.compile(r"\(#(\d+)\)")


def find_issue_by_title(title: str) -> int | None:
    """Recherche une issue GitHub existante par titre exact.

    Parcourt toutes les issues ouvertes. Si le titre correspond exactement,
    retourne le numéro. Sinon, retourne None.
    """
    page = 1
    while True:
        data = gh_get(
            f"/repos/{REPO}/issues",
            {"state": "open", "per_page": 100, "page": page},
        )
        if not data:
            break
        for issue in data:
            if issue.get("title") == title:
                return int(issue["number"])
        if len(data) < 100:
            break
        page += 1
    return None


def update_roadmap_with_issues(
    path: str,
    epic_issues: dict[str, int],
    sprint_issues: dict[str, int] | None = None,
) -> None:
    """Écrit les références (#NUMBER) dans le fichier roadmap.

    Supprime d'abord toutes les anciennes références (#NN) pour éviter les doublons.
    Met à jour les lignes Epic (###) et Sprint (####).
    """
    if sprint_issues is None:
        sprint_issues = {}
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    updated_lines: list[str] = []
    changed = False
    for line in lines:
        new_line = line
        stripped = line.strip()
        if stripped.startswith("### ") or stripped.startswith("#### "):
            base = ISSUE_REF_RE.sub("", stripped).rstrip()
            for title, number in {**epic_issues, **sprint_issues}.items():
                if title in stripped:
                    new_line = base + f" (#{number})\n"
                    if new_line != line:
                        changed = True
                    break
        updated_lines.append(new_line)

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)
        print(
            f"📝 Roadmap mis à jour avec "
            f"{len(epic_issues) + len(sprint_issues)} références d'issues"
        )
    else:
        print("📝 Roadmap déjà à jour (aucune modification)")


# ---------------------------------------------------------------------------
# Parsing du roadmap
# ---------------------------------------------------------------------------

LOT_RE = re.compile(r"^##\s+Lot\s+\d+\s*[\u2014\u2013-]\s*(.+)$")
EPIC_BRACKET_RE = re.compile(
    r"^###\s+(EPIC\s+[\d.]+(?:[+]\s*)?(?:/[A-Z]+)?|"
    r"\u00c9l\u00e9ments critiques manquants|"
    r"Workstreams?|Configuration Engine)"
    r"\s*[\u2014\u2013-]\s*(.+?)"
    r"\s*\[(DONE|IN_PROGRESS|PLANNED|DEFERRED|BLOCKED|PARTIEL|TODO"
    r"|REPORT[EÉ]|ANNUL[EÉ]|À_FAIRE)\]"
)
SPRINT_RE = re.compile(
    r"^####\s+Sprint\s+(.+?)\s*[\u2014\u2013]\s*(.+?)"
    r"\s*\[(DONE|IN_PROGRESS|PLANNED|DEFERRED|BLOCKED|PARTIEL|TODO"
    r"|REPORT[EÉ]|ANNUL[EÉ]|À_FAIRE)\]"
    r"(?:\s*\(#\d+\))?\s*$"
)


def parse_roadmap(path: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    current_lot: str | None = None
    unmatched: list[str] = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            stripped = line.strip()

            if not stripped or stripped.startswith("|") or stripped.startswith("```"):
                continue

            m_lot = LOT_RE.match(stripped)
            if m_lot and not stripped.startswith("###"):
                current_lot = m_lot.group(1).strip()
                items.append(
                    {
                        "type": "lot",
                        "title": current_lot,
                        "status": None,
                        "parent": None,
                        "lot": current_lot,
                        "epic": None,
                    }
                )
                continue

            if stripped.startswith("### "):
                m_epic = EPIC_BRACKET_RE.match(stripped)
                if m_epic:
                    epic_id = m_epic.group(1).strip()
                    epic_title = m_epic.group(2).strip()
                    raw_status = m_epic.group(3).strip().upper()
                    status = status_from_text(raw_status)

                    items.append(
                        {
                            "type": "epic",
                            "title": f"{epic_id} — {epic_title}",
                            "status": status,
                            "parent": current_lot,
                            "lot": current_lot,
                            "epic": epic_id,
                        }
                    )
                    continue

                content = stripped[4:].strip()
                # Remove issue references (#NN)
                content = ISSUE_REF_RE.sub("", content).strip()
                # Remove status brackets [STATUS]
                content = re.sub(r"\s*\[[A-ZÀ-ÿ_ ]+\]\s*", " ", content).strip()
                parts = re.split(r"\s*[·\-]\s*", content, maxsplit=1)
                title_part = parts[0].strip()
                status_part = parts[1].strip() if len(parts) > 1 else ""

                id_match = re.match(
                    r"^(EPIC\s+[\d.]+(?:/[A-Z]+)?|"
                    r"\u00c9l\u00e9ments critiques manquants|"
                    r"Workstreams?|Configuration Engine)",
                    title_part,
                )
                if id_match:
                    epic_id = id_match.group(1)
                    rest = title_part[len(id_match.group(0)) :].strip()
                    if rest.startswith("— "):
                        rest = rest[2:].strip()
                    elif rest.startswith("—"):
                        rest = rest[1:].strip()

                    status = next(
                        (
                            mapped
                            for emoji, mapped in EMOJI_TO_STATUS.items()
                            if emoji in status_part
                        ),
                        status_from_text(status_part),
                    )

                    full_title = f"{epic_id} — {rest}" if rest else epic_id

                    items.append(
                        {
                            "type": "epic",
                            "title": full_title,
                            "status": status,
                            "parent": current_lot,
                            "lot": current_lot,
                            "epic": epic_id,
                        }
                    )
                    continue

            m_sprint = SPRINT_RE.match(stripped)
            if m_sprint:
                sprint_id = f"Sprint {m_sprint.group(1)}"
                raw_sprint_status = m_sprint.group(3).upper()
                sprint_status = status_from_text(raw_sprint_status)
                sprint_title = m_sprint.group(2).strip()
                items.append(
                    {
                        "type": "sprint",
                        "title": f"{sprint_id} — {sprint_title}",
                        "status": sprint_status,
                        "parent": None,
                        "lot": None,
                        "epic": None,
                    }
                )
                continue

            if (stripped.startswith("## ") and not stripped.startswith("## Lot")) or (
                stripped.startswith("#### ") and not stripped.startswith("#### Sprint")
            ):
                unmatched.append(stripped)

    if unmatched:
        print("⚠️  Lignes non reconnues :")
        for u in unmatched:
            print(f"   {u}")

    last_epic_title = None
    for item in items:
        if item["type"] == "epic":
            last_epic_title = item["title"]
        elif item["type"] == "sprint" and last_epic_title:
            item["parent"] = last_epic_title

    return items


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print("🔍 Parsing roadmap...")
    items = parse_roadmap(ROADMAP_PATH)
    lots = [it for it in items if it["type"] == "lot"]
    epics = [it for it in items if it["type"] == "epic"]
    sprints = [it for it in items if it["type"] == "sprint"]
    print(f"   → {len(lots)} Lots, {len(epics)} Epics, {len(sprints)} Sprints")

    print("🔗 Connexion au Project...")
    project_id = get_project_node_id()

    print("📖 Lecture des champs...")
    fields = get_fields(project_id)
    status_field = fields.get("Status")
    epic_field = fields.get("Epic")
    priority_field = fields.get("Priority")

    if not status_field or status_field.get("type") != "SELECT":
        print("❌ Champ 'Status' (select) introuvable dans le Project")
        sys.exit(1)

    def option_ids(field):
        return {opt["name"]: opt["id"] for opt in field.get("options", [])}

    status_opts = option_ids(status_field)
    priority_opts = (
        option_ids(priority_field)
        if priority_field and priority_field.get("type") == "SELECT"
        else {}
    )

    print("📖 Lecture des items existants...")
    existing_items = get_existing_items(project_id)
    print(f"   → {len(existing_items)} items existants")

    print("\n📌 Création des milestones pour les Lots...")
    lot_milestones: dict[str, int] = {}
    for lot in lots:
        ms_number = get_or_create_milestone(lot["title"])
        lot_milestones[lot["title"]] = ms_number
        print(f"   ✅ Milestone: {lot['title']} (#{ms_number})")

    print("\n🐛 Création/liaison des Issues GitHub pour les Epics...")
    repo_id = get_repo_node_id()
    epic_node_ids: dict[str, str | None] = {}
    epic_issues: dict[str, int] = {}
    epic_issue_numbers: dict[str, int] = {}

    for epic in epics:
        title = epic["title"]
        status = epic.get("status")

        if status == "Done":
            print(f"   ⏭️  Epic déjà terminé, pas d'issue: {title}")
            continue

        existing_num = find_issue_by_title(title)
        if existing_num is not None:
            issue_number = existing_num
            print(f"   ℹ️  Epic déjà lié: {title} (#{issue_number})")
            epic_issues[title] = issue_number
            epic_issue_numbers[title] = issue_number
            issue_node_id = get_issue_node_id(repo_id, issue_number)
            project_item_id = add_issue_to_project(project_id, issue_node_id)
            epic_node_ids[title] = project_item_id
            # Tag existing issue with Lot milestone
            parent_lot = epic.get("parent")
            if parent_lot and parent_lot in lot_milestones:
                set_issue_milestone(issue_number, lot_milestones[parent_lot])
            continue

        issue_title = title
        issue_body = (
            f"**Epic:** {epic.get('epic', 'N/A')}\n"
            f"**Lot:** {epic.get('lot', 'N/A')}\n"
            f"**Status:** {status or 'N/A'}\n\n"
            f"Généré automatiquement depuis le roadmap."
        )

        try:
            issue_number, issue_node_id = create_issue(repo_id, issue_title, issue_body)
            project_item_id = add_issue_to_project(project_id, issue_node_id)
            epic_issues[title] = issue_number
            epic_issue_numbers[title] = issue_number
            epic_node_ids[title] = project_item_id
            # Tag new issue with Lot milestone
            parent_lot = epic.get("parent")
            if parent_lot and parent_lot in lot_milestones:
                set_issue_milestone(issue_number, lot_milestones[parent_lot])
            print(f"   ✅ Issue créée et ajoutée au Project: {title} (#{issue_number})")
        except Exception as exc:
            print(f"   ❌ Erreur création issue pour {title}: {exc}")

    print("\n📦 Synchronisation des Epics (champs Project)...")
    for epic in epics:
        title = epic["title"]
        epic_node_id: str | None = epic_node_ids.get(title)
        if not epic_node_id:
            print(f"   ⚠️  Epic sans issue GitHub, skipped: {title}")
            continue

        if epic["status"] and epic["status"] in status_opts:
            set_select_field(
                project_id,
                epic_node_id,
                status_field["id"],
                status_opts[epic["status"]],
            )

        # Ensure milestone is set (handles epics already linked before refactor)
        parent_lot = epic.get("parent")
        if parent_lot and parent_lot in lot_milestones:
            issue_num = epic_issue_numbers.get(title) or epic_issues.get(title, 0)
            if issue_num:
                set_issue_milestone(issue_num, lot_milestones[parent_lot])

        if epic_field and epic.get("epic"):
            set_text_field(project_id, epic_node_id, epic_field["id"], epic["epic"])

        if priority_field and epic["status"] and epic["status"] in PRIORITY_FROM_STATUS:
            prio = PRIORITY_FROM_STATUS[epic["status"]]
            if prio in priority_opts:
                set_select_field(
                    project_id,
                    epic_node_id,
                    priority_field["id"],
                    priority_opts[prio],
                )

        print(f"   ✅ Epic: {epic['title']} [{epic['status'] or 'N/A'}]")

    print("\n🐛 Création/liaison des Issues GitHub pour les Sprints...")
    sprint_issues: dict[str, int] = {}
    for sprint in sprints:
        title = sprint["title"]
        status = sprint.get("status")
        parent_epic_title = sprint.get("parent")
        parent_number = epic_issue_numbers.get(parent_epic_title) if parent_epic_title else None

        if status == "Done":
            print(f"   ⏭️  Sprint déjà terminé, pas d'issue: {title}")
            continue

        issue_title = title
        issue_body = (
            f"**Sprint:** {sprint.get('epic', 'N/A')}\n"
            f"**Lot:** {sprint.get('lot', 'N/A')}\n"
            f"**Status:** {status or 'N/A'}\n"
        )
        if parent_epic_title:
            issue_body += f"\nParent: {parent_epic_title}"

        # Check if issue already exists by title
        existing_sprint_num = find_issue_by_title(issue_title)
        if existing_sprint_num is not None:
            issue_number = existing_sprint_num
            print(f"   ℹ️  Sprint déjà existante: {title} (#{issue_number})")
        else:
            # Create new issue
            try:
                issue_number, issue_node_id = create_issue(repo_id, issue_title, issue_body)
                print(f"   ✅ Issue créée: {title} (#{issue_number})")
            except Exception as exc:
                print(f"   ❌ Erreur création issue pour {title}: {exc}")
                continue

        # Add to Project
        sprint_project_item_id: str | None = None
        try:
            sprint_project_item_id = add_issue_to_project(
                project_id, get_issue_node_id(repo_id, issue_number)
            )
        except Exception as exc:
            print(f"   ⚠️  Issue non ajoutée au Project: {title}: {exc}")

        # Tag with Lot milestone
        if parent_epic_title:
            epic_data = next((e for e in epics if e["title"] == parent_epic_title), None)
            if epic_data:
                lot_title = epic_data.get("parent")
                if lot_title and lot_title in lot_milestones:
                    set_issue_milestone(issue_number, lot_milestones[lot_title])

        # Try to link as sub-issue to parent Epic
        if parent_number and parent_number != issue_number:
            try:
                if is_sub_issue(parent_number, issue_number):
                    print(
                        f"   ✅ Sub-issue déjà liée à #{parent_number}: {title} (#{issue_number})"
                    )
                elif add_sub_issue(parent_number, issue_number):
                    print(f"   ✅ Sub-issue liée à #{parent_number}: {title} (#{issue_number})")
                else:
                    print(
                        f"   ⚠️  Sub-issue non activé, issue standalone: {title} (#{issue_number})"
                    )
            except Exception as exc:
                print(f"   ⚠️  Sub-issue échouée, issue standalone: {title}: {exc}")

        # Set Project fields
        if sprint_project_item_id:
            if sprint["status"] and sprint["status"] in status_opts:
                set_select_field(
                    project_id,
                    sprint_project_item_id,
                    status_field["id"],
                    status_opts[sprint["status"]],
                )

            if priority_field and sprint["status"] and sprint["status"] in PRIORITY_FROM_STATUS:
                prio = PRIORITY_FROM_STATUS[sprint["status"]]
                if prio in priority_opts:
                    set_select_field(
                        project_id,
                        sprint_project_item_id,
                        priority_field["id"],
                        priority_opts[prio],
                    )

        sprint_issues[title] = issue_number

    if epic_issues or sprint_issues:
        update_roadmap_with_issues(ROADMAP_PATH, epic_issues, sprint_issues)

    print("\n🎉 Synchronisation terminée !")
    print(f"   → {len(epic_issues)} Epics (vraies issues)")
    print(f"   → {len(sprint_issues)} Sprints (vraies issues ou sub-issues)")


if __name__ == "__main__":
    if sys.stdout.encoding != "utf-8" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
