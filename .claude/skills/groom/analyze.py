#!/usr/bin/env python3
"""Read project-board state + issue states, emit structured groom proposals.

Output is a JSON object grouped by category — the `/groom` skill reads it,
presents to the user, and asks for category-level opt-in before applying.

Phase 1 heuristics (#683):

- **needs_triage** — item has no Priority or no Workstream set
- **drift_done_open** — Status=Done but linked issue is OPEN; either close
  the issue or move the item back to Todo/In Progress
- **drift_closed_not_done** — linked issue is CLOSED but Status≠Done; move
  the item to Done
- **stale_p3** — P3-someday items whose project-item ``updatedAt`` > 90
  days ago; candidate for review or closure
- **idle_p0_p1** — P0-now or P1-this-week items in Todo or In Progress
  whose ``updatedAt`` > 21 days ago; candidate for re-prioritization or
  closure
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any

PROJECT_NUMBER = "5"
OWNER = "@me"
PROJECT_TITLE = "Katana MCP — Rolling Backlog"

STALE_P3_DAYS = 90
IDLE_P0_P1_DAYS = 21


def run_gh(args: list[str]) -> str:
    proc = subprocess.run(["gh", *args], check=True, capture_output=True, text=True)
    return proc.stdout


def fetch_project_items() -> list[dict[str, Any]]:
    """Return the full project-item list with all fields populated."""
    raw = run_gh(
        [
            "project",
            "item-list",
            PROJECT_NUMBER,
            "--owner",
            OWNER,
            "--limit",
            "300",
            "--format",
            "json",
        ]
    )
    data = json.loads(raw)
    return data.get("items", [])


def fetch_issue_states(issue_numbers: set[int]) -> dict[int, dict[str, Any]]:
    """Batch-fetch ``state`` (+ has-open-PR signal) for each issue number.

    Returns ``{number: {state: "open"|"closed", has_open_pr: bool,
    updated_at: ISO8601}}``. Skips fetches for numbers in
    ``issue_numbers`` that aren't actually issues (e.g., PR numbers) —
    ``gh issue view`` errors on those and we just omit them.
    """
    out: dict[int, dict[str, Any]] = {}
    for num in sorted(issue_numbers):
        try:
            raw = run_gh(
                [
                    "issue",
                    "view",
                    str(num),
                    "--json",
                    "state,updatedAt,closedByPullRequestsReferences",
                ]
            )
            data = json.loads(raw)
            prs = data.get("closedByPullRequestsReferences") or []
            has_open_pr = any(pr.get("state") == "OPEN" for pr in prs)
            out[num] = {
                "state": (data.get("state") or "").lower(),
                "updated_at": data.get("updatedAt"),
                "has_open_pr": has_open_pr,
            }
        except subprocess.CalledProcessError:
            # Not an issue (PR or invalid number) — skip silently.
            continue
    return out


def parse_issue_number(url: str | None) -> int | None:
    if not url:
        return None
    match = re.search(r"/issues/(\d+)$", url)
    return int(match.group(1)) if match else None


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def days_since(value: str | None, *, now: datetime) -> int | None:
    parsed = parse_iso(value)
    if parsed is None:
        return None
    return (now - parsed).days


def classify_items(
    items: list[dict[str, Any]],
    issue_states: dict[int, dict[str, Any]],
    now: datetime,
) -> dict[str, list[dict[str, Any]]]:
    """Apply all heuristics to the project items; return grouped proposals."""
    out: dict[str, list[dict[str, Any]]] = {
        "needs_triage": [],
        "drift_done_open": [],
        "drift_closed_not_done": [],
        "stale_p3": [],
        "idle_p0_p1": [],
    }

    for item in items:
        content = item.get("content") or {}
        number = content.get("number")
        title = content.get("title") or item.get("title") or ""
        url = content.get("url")
        item_id = item.get("id")
        status = (item.get("status") or "").strip()
        priority = (item.get("priority") or "").strip()
        workstream = (item.get("workstream") or "").strip()
        updated_at = item.get("updatedAt") or content.get("updatedAt")
        ago_days = days_since(updated_at, now=now)

        # Skip draft items (no linked issue/PR). They don't have a state to
        # cross-reference and shouldn't normally exist on this board.
        if number is None or url is None:
            continue

        # Only operate on issues — PRs land on the board but their lifecycle
        # is handled by the "Pull request merged" workflow and they shouldn't
        # surface in groom proposals.
        issue_no = parse_issue_number(url)
        if issue_no is None:
            continue

        base = {
            "number": issue_no,
            "title": title,
            "url": url,
            "item_id": item_id,
            "status": status or "(unset)",
            "priority": priority or "(unset)",
            "workstream": workstream or "(unset)",
            "updated_at": updated_at,
            "ago_days": ago_days,
        }

        # Heuristic 1: needs triage
        if not priority or not workstream:
            out["needs_triage"].append(base)

        # Cross-reference heuristics need the linked issue's state.
        issue_info = issue_states.get(issue_no)
        issue_state = (issue_info or {}).get("state")

        # Heuristic 2: Done but issue open
        if status.lower() == "done" and issue_state == "open":
            out["drift_done_open"].append(base)

        # Heuristic 3: issue closed but project status != Done
        if issue_state == "closed" and status.lower() != "done":
            out["drift_closed_not_done"].append(base)

        # Heuristic 4: stale P3
        if (
            priority.lower().startswith("p3")
            and ago_days is not None
            and ago_days > STALE_P3_DAYS
        ):
            out["stale_p3"].append(base)

        # Heuristic 5: idle P0/P1
        is_active = priority.lower().startswith(("p0", "p1"))
        is_open_status = status.lower() in ("todo", "in progress")
        has_open_pr = (issue_info or {}).get("has_open_pr", False)
        if (
            is_active
            and is_open_status
            and ago_days is not None
            and ago_days > IDLE_P0_P1_DAYS
            and not has_open_pr
        ):
            out["idle_p0_p1"].append(base)

    return out


def main() -> int:
    now = datetime.now(tz=UTC)
    items = fetch_project_items()
    issue_numbers: set[int] = set()
    for item in items:
        content = item.get("content") or {}
        issue_no = parse_issue_number(content.get("url"))
        if issue_no is not None:
            issue_numbers.add(issue_no)

    issue_states = fetch_issue_states(issue_numbers)
    proposals = classify_items(items, issue_states, now)

    summary = {category: len(rows) for category, rows in proposals.items()}
    output = {
        "project_number": PROJECT_NUMBER,
        "project_title": PROJECT_TITLE,
        "analyzed_at": now.isoformat(),
        "summary": summary,
        "total_items": len(items),
        "proposals": proposals,
    }
    json.dump(output, sys.stdout, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
