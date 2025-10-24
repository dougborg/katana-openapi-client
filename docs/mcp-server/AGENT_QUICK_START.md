# MCP Server Implementation - Agent Quick Start Guide

This guide helps copilot agents understand how to work on the Katana MCP Server
implementation.

## Project Overview

We're building an MCP (Model Context Protocol) server that exposes Katana Manufacturing
ERP functionality to Claude Code and other MCP clients. This is a **monorepo project**
using **uv workspace** to manage both the client library and MCP server packages.

## Key Resources

- **ADR-010**: [docs/adr/0010-katana-mcp-server.md](../adr/0010-katana-mcp-server.md) -
  Full architectural decision
- **Implementation Plan**:
  [docs/mcp-server/IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Dependency graph
  and strategy
- **GitHub Milestone**:
  [MCP Server v0.1.0 MVP](https://github.com/dougborg/katana-openapi-client/milestone/1)
- **Issues**: GitHub #32-55 (24 issues total)

## Understanding Dependencies

**CRITICAL**: Every issue has dependencies clearly marked in the "Dependencies" section.

**Example**:

```markdown
## Dependencies
- **Blocked by**: #32, #33
- **Blocks**: #35, #36
```

**Rules**:

1. ✅ **Only work on issues with no blockers** OR **all blockers are closed**
1. ❌ **Never start an issue if ANY blocker is still open**
1. 📢 **Comment on the issue when you start** work to avoid conflicts
1. ✅ **Close the issue when complete** to unblock dependent issues

## Current Work Queue (In Dependency Order)

### Ready to Start Now (No Blockers):

**#32: Set up uv workspace for monorepo**

- **Time**: 2-4h
- **Priority**: P0-Critical
- **What**: Add `[tool.uv.workspace]` configuration to root `pyproject.toml`
- **Blocks**: #33

### Ready After #32 Closes:

**#33: Create katana_mcp_server package structure**

- **Time**: 2-3h
- **Priority**: P0-Critical
- **Blocked by**: #32
- **Blocks**: #34, #54

### Ready After #33 Closes:

**#34: Implement basic FastMCP server with authentication**

- **Time**: 4-6h
- **Priority**: P0-Critical
- **Blocked by**: #33
- **Blocks**: #35, #38, #41, #44 (all tools)

### Parallelizable After #34 Closes:

Once #34 is complete, **4 agents can work in parallel**:

- **Agent A**: #35 (check_inventory tool)
- **Agent B**: #38 (create_sales_order tool)
- **Agent C**: #41 (create_purchase_order tool)
- **Agent D**: #44 (create_manufacturing_order tool)

## Issue Labeling Guide

Each issue has multiple labels to help you understand its scope:

**Type Labels**:

- `infrastructure` - Setup and configuration
- `tool` - MCP tool implementation
- `resource` - MCP resource implementation
- `prompt` - MCP prompt implementation
- `documentation` - Documentation
- `testing` - Tests
- `release` - Release tasks

**Domain Labels**:

- `inventory`, `sales-orders`, `purchase-orders`, `manufacturing`, `server`

**Priority Labels**:

- `p0-critical` - Must be done first
- `p1-high` - Important
- `p2-medium` - Standard
- `p3-low` - Nice to have

**Project Label**:

- `mcp-server` - All MCP server issues

## How to Work on an Issue

### 1. Check Dependencies

```bash
# View the issue
gh issue view 32

# Check if blockers are closed
gh issue list --label "mcp-server" --state open
```

### 2. Claim the Issue

```bash
# Comment on the issue
gh issue comment 32 --body "🤖 Starting work on this issue"

# Assign to yourself (optional)
gh issue edit 32 --add-assignee @me
```

### 3. Read the Context

Each issue links to:

- ADR-010 for architectural decisions
- Implementation Plan for dependency visualization
- Specific cookbook sections or examples when relevant

### 4. Implementation Checklist

Every issue has **Acceptance Criteria** checkboxes. For example:

```markdown
## Acceptance Criteria
- [ ] Add [tool.uv.workspace] to root pyproject.toml
- [ ] Configure workspace members
- [ ] Verify uv sync works across both packages
- [ ] Document workspace setup
```

**Complete ALL criteria** before closing the issue.

### 5. Testing Requirements

Most issues require tests:

- **Unit tests**: Test with mocked KatanaClient
- **Integration tests**: Test with real API (requires `KATANA_API_KEY`)

### 6. Submit Your Work

```bash
# Create a branch
git checkout -b mcp-32-uv-workspace

# Make your changes
# ...

# Commit with conventional commits - ALWAYS USE (mcp) SCOPE
git commit -m "feat(mcp): set up uv workspace for monorepo (#32)"

# Push and create PR
git push origin mcp-32-uv-workspace
gh pr create --title "MCP-32: Set up uv workspace" --body "Closes #32"
```

**IMPORTANT:** Always use the `(mcp)` scope for MCP server changes! This ensures the MCP
package is released when your changes are merged.

Examples:

- ✅ `feat(mcp): add inventory tool` - Correct
- ✅ `fix(mcp): resolve auth error` - Correct
- ❌ `feat: add inventory tool` - Wrong (will release client instead)
- ❌ `feat(inventory): add tool` - Wrong scope

### 7. Close the Issue

```bash
# After PR is merged
gh issue close 32 --comment "✅ Completed and merged"
```

## Code Patterns to Follow

### Tool Implementation Pattern

```python
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel

# Return type model
class InventoryStatus(BaseModel):
    sku: str
    in_stock: int
    available: int
    location: str | None = None

# Tool implementation
@mcp.tool()
async def check_inventory(sku: str, ctx: Context) -> InventoryStatus:
    """Check inventory status for a specific SKU."""
    # Report progress
    await ctx.report_progress(0.3, 1.0)

    # Use KatanaClient
    async with KatanaClient() as client:
        # Implementation...
        pass
```

### Testing Pattern

```python
from unittest.mock import AsyncMock, patch
import pytest

@pytest.mark.asyncio
async def test_check_inventory():
    """Test check_inventory tool with mocked client."""
    with patch('katana_mcp.tools.inventory.KatanaClient') as mock_client:
        # Setup mock
        mock_client.return_value.__aenter__.return_value = mock_client

        # Test
        result = await check_inventory("SKU-123", mock_context)

        # Assert
        assert result.sku == "SKU-123"
        assert result.in_stock >= 0
```

## Common Questions

**Q: Can I work on multiple issues at once?** A: Yes, but only if they don't depend on
each other. Check the dependency graph in IMPLEMENTATION_PLAN.md.

**Q: What if my blocker is assigned to someone else who hasn't started?** A: Comment on
the blocker issue asking for status. Consider taking it on if it's been idle.

**Q: Where do I find the Katana API documentation?** A: Check
`katana_public_api_client/api/` for all generated endpoints, or see the Cookbook
(docs/COOKBOOK.md) for patterns.

**Q: How do I test with a real Katana API?** A: Set `KATANA_API_KEY=your-key` in `.env`.
Integration tests marked with `@pytest.mark.integration` use this.

**Q: What version of Python?** A: Python 3.11+ required. Use `uv sync` to set up the
environment.

## Getting Help

1. **Check the docs first**:

   - [ADR-010](../adr/0010-katana-mcp-server.md) - Why we made these decisions
   - [Implementation Plan](IMPLEMENTATION_PLAN.md) - Dependency graph and strategy
   - [Cookbook](../COOKBOOK.md) - Patterns for using the Katana client

1. **Ask in the issue**: Comment with your question

1. **Look at related issues**: Other tool implementations will have similar patterns

## Pro Tips for Agents

✅ **DO**:

- Read the entire issue before starting
- Check ALL dependencies are closed
- Follow the acceptance criteria exactly
- Write tests
- Update documentation
- Use conventional commit messages

❌ **DON'T**:

- Start an issue with open blockers
- Skip tests
- Modify generated code in `katana_public_api_client/api/` or
  `katana_public_api_client/models/`
- Change issue dependencies without discussion

## Success Metrics

A successful implementation:

- ✅ All acceptance criteria checked off
- ✅ Unit tests passing (80%+ coverage)
- ✅ Integration tests passing (if applicable)
- ✅ Documentation updated
- ✅ PR reviewed and merged
- ✅ Issue closed
- ✅ Dependent issues unblocked

______________________________________________________________________

**Ready to start?** Check the
[GitHub milestone](https://github.com/dougborg/katana-openapi-client/milestone/1) for
available issues!
