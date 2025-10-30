#!/usr/bin/env python3
"""
Create GitHub issues for MCP server implementation.

This script creates all 24 issues for the Katana MCP Server implementation
as planned in docs/mcp-server/MCP_V0.1.0_IMPLEMENTATION_PLAN.md.

Usage:
    uv run python scripts/create_mcp_issues.py
    uv run python scripts/create_mcp_issues.py --dry-run
"""

import argparse
import subprocess
from dataclasses import dataclass


@dataclass
class Issue:
    """Represents a GitHub issue."""

    number: int
    title: str
    body: str
    labels: list[str]
    milestone: str
    estimate_hours: str
    blocked_by: list[int]


# Issue definitions
ISSUES = [
    Issue(
        number=1,
        title="Set up uv workspace for monorepo",
        body="""## Description

Set up uv workspace configuration to enable monorepo management for both `katana-openapi-client` and `katana-mcp-server` packages.

## Acceptance Criteria

- [ ] Add `[tool.uv.workspace]` to root `pyproject.toml`
- [ ] Configure workspace members: `["katana_public_api_client", "katana_mcp_server"]`
- [ ] Verify `uv sync` works across both packages
- [ ] Update `.gitignore` if needed for workspace artifacts
- [ ] Verify existing client package still works
- [ ] Document workspace setup in README

## Implementation Notes

Reference: [uv workspaces documentation](https://docs.astral.sh/uv/concepts/workspaces/)

Add to root `pyproject.toml`:
```toml
[tool.uv.workspace]
members = ["katana_public_api_client", "katana_mcp_server"]
```

## Dependencies

- **Blocked by**: None (can start immediately)
- **Blocks**: #2

## Related Documentation

- [ADR-010: Katana MCP Server](docs/adr/0010-katana-mcp-server.md)
- [MCP v0.1.0 Implementation Plan](docs/mcp-server/MCP_V0.1.0_IMPLEMENTATION_PLAN.md)
""",
        labels=["infrastructure", "mcp-server", "p0-critical"],
        milestone="MCP Server v0.1.0 MVP",
        estimate_hours="2-4h",
        blocked_by=[],
    ),
    Issue(
        number=2,
        title="Create katana_mcp_server package structure",
        body="""## Description

Create the directory structure and initial files for the `katana-mcp-server` package within the monorepo.

## Acceptance Criteria

- [ ] Create directory: `katana_mcp_server/src/katana_mcp/`
- [ ] Create subdirectories: `tools/`, `resources/`, `prompts/`
- [ ] Create `__init__.py` files in all directories
- [ ] Create `katana_mcp_server/pyproject.toml` with dependencies
- [ ] Create `katana_mcp_server/README.md` with installation instructions
- [ ] Create `katana_mcp_server/tests/` directory
- [ ] Verify package can be imported after `uv sync`

## Implementation Notes

**Directory Structure:**
```
katana_mcp_server/
├── pyproject.toml
├── README.md
├── src/
│   └── katana_mcp/
│       ├── __init__.py
│       ├── server.py (placeholder)
│       ├── tools/
│       │   └── __init__.py
│       ├── resources/
│       │   └── __init__.py
│       └── prompts/
│           └── __init__.py
└── tests/
    └── __init__.py
```

**pyproject.toml:**
```toml
[project]
name = "katana-mcp-server"
version = "0.1.0"
description = "MCP server for Katana Manufacturing ERP"
requires-python = ">=3.11"
dependencies = [
    "katana-openapi-client",
    "mcp>=1.0.0",
    "pydantic>=2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Dependencies

- **Blocked by**: #1
- **Blocks**: #3, #23

## Related Documentation

- [ADR-010: Architecture](docs/adr/0010-katana-mcp-server.md#architecture)
""",
        labels=["infrastructure", "mcp-server", "p0-critical"],
        milestone="MCP Server v0.1.0 MVP",
        estimate_hours="2-3h",
        blocked_by=[1],
    ),
    Issue(
        number=3,
        title="Implement basic FastMCP server with authentication",
        body="""## Description

Create the core FastMCP server with environment-based authentication and KatanaClient initialization.

## Acceptance Criteria

- [ ] Create `server.py` with FastMCP initialization
- [ ] Implement environment-based authentication (KATANA_API_KEY, KATANA_BASE_URL)
- [ ] Initialize KatanaClient with proper error handling
- [ ] Add server metadata (name, version)
- [ ] Create simple health check or info endpoint
- [ ] Write unit tests for server initialization
- [ ] Write unit tests for authentication failure scenarios
- [ ] Document required environment variables

## Implementation Notes

**Basic Server Structure:**
```python
from mcp.server.fastmcp import FastMCP
from katana_public_api_client import KatanaClient
import os

mcp = FastMCP("katana-erp")

def get_katana_client() -> KatanaClient:
    api_key = os.getenv("KATANA_API_KEY")
    if not api_key:
        raise ValueError("KATANA_API_KEY environment variable is required")

    base_url = os.getenv("KATANA_BASE_URL", "https://api.katanamrp.com/v1")
    return KatanaClient(api_key=api_key, base_url=base_url)
```

**Testing:**
- Mock environment variables
- Test missing API key raises error
- Test valid configuration creates client
- Test client initialization

## Dependencies

- **Blocked by**: #2
- **Blocks**: #4, #7, #10, #13 (all tools)

## Related Documentation

- [FastMCP Documentation](https://github.com/modelcontextprotocol/python-sdk#fastmcp)
- [KatanaClient Guide](docs/KATANA_CLIENT_GUIDE.md)
""",
        labels=["server", "mcp-server", "p0-critical"],
        milestone="MCP Server v0.1.0 MVP",
        estimate_hours="4-6h",
        blocked_by=[2],
    ),
    Issue(
        number=4,
        title="Implement check_inventory tool",
        body="""## Description

Implement the `check_inventory` tool to check stock levels for a specific SKU.

## Acceptance Criteria

- [ ] Create `tools/inventory.py`
- [ ] Implement `check_inventory(sku: str)` with proper type hints
- [ ] Define Pydantic model for return type (InventoryStatus)
- [ ] Use KatanaClient to fetch inventory data
- [ ] Add progress reporting via MCP context
- [ ] Handle errors gracefully (SKU not found, API errors)
- [ ] Write unit tests with mocked KatanaClient
- [ ] Write integration test (requires KATANA_API_KEY)
- [ ] Add docstring with usage examples

## Implementation Notes

**Pydantic Model:**
```python
from pydantic import BaseModel

class InventoryStatus(BaseModel):
    sku: str
    in_stock: int
    available: int
    location: str | None = None
    reorder_point: int | None = None
    status: str  # "in_stock", "low_stock", "out_of_stock"
```

**Tool Implementation:**
```python
from mcp.server.fastmcp import FastMCP, Context

@mcp.tool()
async def check_inventory(sku: str, ctx: Context) -> InventoryStatus:
    \"\"\"Check inventory status for a specific SKU.\"\"\"
    await ctx.report_progress(0.3, 1.0)
    # Implementation using KatanaClient
    # Reference: Cookbook §2.1 (Inventory queries)
```

**API Endpoints to Use:**
- `get_all_variants` (search by SKU)
- `get_all_inventory_point` (get stock levels)

## Dependencies

- **Blocked by**: #3
- **Blocks**: #5, #6, #16, #19, #20, #21

## Related Documentation

- [Cookbook §2.1: Querying Inventory](docs/COOKBOOK.md)
- [API: get_all_inventory_point](katana_public_api_client/api/inventory/)
""",
        labels=["tool", "inventory", "mcp-server", "p1-high"],
        milestone="MCP Server v0.1.0 MVP",
        estimate_hours="4-6h",
        blocked_by=[3],
    ),
    Issue(
        number=5,
        title="Implement list_low_stock_items tool",
        body="""## Description

Implement the `list_low_stock_items` tool to find products below their reorder point.

## Acceptance Criteria

- [ ] Add `list_low_stock_items(threshold: int = 10)` to `tools/inventory.py`
- [ ] Define Pydantic model for return type (list of LowStockItem)
- [ ] Implement pagination handling for large results
- [ ] Add progress reporting
- [ ] Handle edge cases (no low stock items)
- [ ] Write unit and integration tests
- [ ] Add docstring with examples

## Implementation Notes

**Pydantic Model:**
```python
class LowStockItem(BaseModel):
    sku: str
    name: str
    in_stock: int
    reorder_point: int
    difference: int  # How much below reorder point
```

**Implementation Reference:**
- See `examples/low_stock_monitoring.py` for logic
- Use `get_all_inventory_point` endpoint
- Filter where `in_stock < reorder_point`

## Dependencies

- **Blocked by**: #4
- **Blocks**: #20

## Related Documentation

- [Example: Low Stock Monitoring](examples/low_stock_monitoring.py)
""",
        labels=["tool", "inventory", "mcp-server", "p1-high"],
        milestone="MCP Server v0.1.0 MVP",
        estimate_hours="4-6h",
        blocked_by=[4],
    ),
    Issue(
        number=6,
        title="Implement search_products tool",
        body="""## Description

Implement the `search_products` tool to search products by name or SKU.

## Acceptance Criteria

- [ ] Add `search_products(query: str, limit: int = 50)` to `tools/inventory.py`
- [ ] Define Pydantic model for return type (list of Product)
- [ ] Implement search logic (by name and SKU)
- [ ] Add progress reporting
- [ ] Handle no results gracefully
- [ ] Write unit and integration tests
- [ ] Add docstring with examples

## Implementation Notes

**Pydantic Model:**
```python
class Product(BaseModel):
    id: int
    sku: str
    name: str
    category: str | None = None
    in_stock: int
```

**API Endpoints:**
- `get_all_products` or `get_all_variants`
- Implement client-side filtering for search

## Dependencies

- **Blocked by**: #4
- **Blocks**: #20

## Related Documentation

- [API: Products](katana_public_api_client/api/product/)
""",
        labels=["tool", "inventory", "mcp-server", "p2-medium"],
        milestone="MCP Server v0.1.0 MVP",
        estimate_hours="4-6h",
        blocked_by=[4],
    ),
]


def create_issue(issue: Issue, dry_run: bool = False) -> dict[str, str | int]:
    """Create a GitHub issue using gh CLI."""
    # Build labels string
    labels = ",".join(issue.labels)

    # Build body with metadata
    full_body = f"""{issue.body}

---
**Estimate**: {issue.estimate_hours}
**Milestone**: {issue.milestone}
"""

    if dry_run:
        print(f"\n{'=' * 80}")
        print(f"Would create issue #{issue.number}: {issue.title}")
        print(f"Labels: {labels}")
        print(f"Milestone: {issue.milestone}")
        if issue.blocked_by:
            print(f"Blocked by: {', '.join(f'#{n}' for n in issue.blocked_by)}")
        print(f"\n{full_body}")
        return {"number": issue.number, "url": "(dry-run)"}

    # Create issue with gh CLI
    cmd = [
        "gh",
        "issue",
        "create",
        "--title",
        issue.title,
        "--body",
        full_body,
        "--label",
        labels,
    ]

    # Note: Milestone assignment may require --milestone flag if supported
    # For now, we'll add it to the body and assign manually if needed

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)

    # Parse issue URL from output
    issue_url = result.stdout.strip()

    print(f"✓ Created #{issue.number}: {issue.title}")
    print(f"  URL: {issue_url}")

    return {"number": issue.number, "url": issue_url}


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create MCP server GitHub issues")
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
        default=len(ISSUES),
        help=f"End at issue number (default: {len(ISSUES)})",
    )

    args = parser.parse_args()

    print(f"Creating MCP Server issues #{args.start}-{args.end}")
    if args.dry_run:
        print("DRY RUN MODE - No issues will be created")
    print()

    created_issues = []

    for issue in ISSUES[args.start - 1 : args.end]:
        try:
            result = create_issue(issue, dry_run=args.dry_run)
            created_issues.append(result)
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to create #{issue.number}: {issue.title}")
            print(f"  Error: {e.stderr}")
            break
        except Exception as e:
            print(f"✗ Unexpected error creating #{issue.number}: {e}")
            break

    print(f"\n{'=' * 80}")
    print(f"Created {len(created_issues)} issues")

    if not args.dry_run:
        print("\nNext steps:")
        print("1. Create milestone: gh issue milestone create 'MCP Server v0.1.0 MVP'")
        print("2. Assign milestone to issues")
        print("3. Set up GitHub Project board for dependency visualization")
        print("4. Review and assign issues to agents")


if __name__ == "__main__":
    main()
