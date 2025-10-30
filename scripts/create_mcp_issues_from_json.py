#!/usr/bin/env python3
"""
Create GitHub issues for MCP server implementation from JSON data.

Usage:
    uv run python scripts/create_mcp_issues_from_json.py
    uv run python scripts/create_mcp_issues_from_json.py --dry-run
    uv run python scripts/create_mcp_issues_from_json.py --start 1 --end 3
"""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def format_issue_body(issue: dict[str, Any]) -> str:
    """Format the issue body from JSON data."""
    body_parts = []

    # Description
    body_parts.append("## Description\n")
    body_parts.append(f"{issue['description']}\n")

    # Acceptance Criteria
    body_parts.append("\n## Acceptance Criteria\n")
    for criterion in issue["acceptance_criteria"]:
        body_parts.append(f"- [ ] {criterion}\n")

    # Dependencies
    body_parts.append("\n## Dependencies\n")
    if issue["blocked_by"]:
        blocked_by_str = ", ".join(f"#{num}" for num in issue["blocked_by"])
        body_parts.append(f"- **Blocked by**: {blocked_by_str}\n")
    else:
        body_parts.append("- **Blocked by**: None (can start immediately)\n")

    # Related Documentation
    body_parts.append("\n## Related Documentation\n")
    body_parts.append(
        "- [ADR-010: Katana MCP Server](docs/adr/0010-katana-mcp-server.md)\n"
    )
    body_parts.append(
        "- [MCP v0.1.0 Implementation Plan](docs/mcp-server/MCP_V0.1.0_IMPLEMENTATION_PLAN.md)\n"
    )

    # Metadata footer
    body_parts.append("\n---\n")
    body_parts.append(f"**Estimate**: {issue['estimate']}\n")
    body_parts.append(f"**Issue Number**: #{issue['number']}\n")

    return "".join(body_parts)


def create_issue(issue: dict[str, Any], dry_run: bool = False) -> dict[str, str | int]:
    """Create a GitHub issue using gh CLI."""
    title = f"MCP-{issue['number']:02d}: {issue['title']}"
    body = format_issue_body(issue)
    labels = ",".join(issue["labels"])

    if dry_run:
        print(f"\n{'=' * 80}")
        print(f"Would create: {title}")
        print(f"Labels: {labels}")
        print(f"Blocked by: {issue['blocked_by'] if issue['blocked_by'] else 'None'}")
        print(f"\n{body[:500]}...")  # First 500 chars
        return {"number": issue["number"], "url": "(dry-run)"}

    # Create issue with gh CLI
    cmd = [
        "gh",
        "issue",
        "create",
        "--title",
        title,
        "--body",
        body,
        "--label",
        labels,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issue_url = result.stdout.strip()

        print(f"✓ Created: {title}")
        print(f"  URL: {issue_url}")

        return {"number": issue["number"], "url": issue_url, "title": title}
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to create: {title}")
        print(f"  Error: {e.stderr}")
        raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create MCP server GitHub issues from JSON"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print issues without creating them",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Start at issue number (default: 1)",
    )
    parser.add_argument(
        "--end",
        type=int,
        help="End at issue number (default: all)",
    )
    parser.add_argument(
        "--json-file",
        type=str,
        required=True,
        help="Path to issues JSON file",
    )

    args = parser.parse_args()

    # Load issues from JSON
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"Error: JSON file not found: {json_path}")
        return 1

    with open(json_path) as f:
        all_issues = json.load(f)

    # Filter by range
    end = args.end if args.end else len(all_issues)
    issues_to_create = [
        issue for issue in all_issues if args.start <= issue["number"] <= end
    ]

    print(f"Creating MCP Server issues #{args.start}-{end}")
    print(f"Total issues to create: {len(issues_to_create)}")
    if args.dry_run:
        print("DRY RUN MODE - No issues will be created\n")

    created_issues = []
    failed_issues = []

    for issue in issues_to_create:
        try:
            result = create_issue(issue, dry_run=args.dry_run)
            created_issues.append(result)
        except Exception as e:
            print(f"✗ Unexpected error creating #{issue['number']}: {e}")
            failed_issues.append(issue["number"])
            # Continue with next issue instead of breaking

    # Summary
    print(f"\n{'=' * 80}")
    print(f"✓ Successfully created: {len(created_issues)} issues")
    if failed_issues:
        print(f"✗ Failed: {len(failed_issues)} issues: {failed_issues}")

    if not args.dry_run and created_issues:
        print("\nNext steps:")
        print("1. Create milestone: gh issue milestone create 'MCP Server v0.1.0 MVP'")
        print("2. Assign milestone to issues:")
        print("   gh issue edit <issue-number> --milestone 'MCP Server v0.1.0 MVP'")
        print("3. Set up GitHub Project board for dependency visualization")
        print("4. Review and assign issues to copilot agents")
        print("\nCreated issues:")
        for issue in created_issues:
            print(f"  - {issue['title']}: {issue['url']}")

    return 0 if not failed_issues else 1


if __name__ == "__main__":
    exit(main())
