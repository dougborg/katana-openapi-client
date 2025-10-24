# MCP Server v0.1.0-alpha - Agent Assignments

## Overview

This document tracks the assignment of "Tall Thin Man" issues to GitHub Copilot agents
for parallel execution.

**Goal**: Build a deployable MCP server with 3 inventory tools as quickly as possible.

## Batch 1: Parallel Execution (START HERE)

These 3 issues can be worked on simultaneously by 3 different agents.

### Agent 1: Issue #35 - check_inventory tool

- **Status**: Ready to start
- **Estimate**: 2-3 hours
- **File**: `katana_mcp_server/src/katana_mcp/tools/inventory.py`
- **Dependencies**: ✅ All met (#58, #60 Phase 1 complete in v0.22.0)
- **Issue**: https://github.com/dougborg/katana-openapi-client/issues/35
- **Spec**: See issue body for complete implementation code

**Key Points**:

- Create new file `tools/inventory.py`
- Thin wrapper around `client.inventory.check_stock()`
- Pydantic models: `CheckInventoryRequest`, `StockInfo`
- FastMCP `@mcp.tool()` decorator

______________________________________________________________________

### Agent 2: Issue #36 - list_low_stock_items tool

- **Status**: Ready to start (can work in parallel with Agent 1)
- **Estimate**: 2-3 hours
- **File**: `katana_mcp_server/src/katana_mcp/tools/inventory.py` (same file)
- **Dependencies**: ✅ All met
- **Issue**: https://github.com/dougborg/katana-openapi-client/issues/36
- **Spec**: See issue body for complete implementation code

**Key Points**:

- Add to same `tools/inventory.py` file as #35
- Thin wrapper around `client.inventory.low_stock()`
- Pydantic models: `LowStockRequest`, `LowStockItem`, `LowStockResponse`
- Implements pagination with `limit` parameter

**Coordination**: If Agent 1 is working on `inventory.py`, this agent should wait for
file creation or coordinate merge.

______________________________________________________________________

### Agent 3: Issue #37 - search_products tool

- **Status**: Ready to start (can work in parallel with Agents 1 & 2)
- **Estimate**: 2-3 hours
- **File**: `katana_mcp_server/src/katana_mcp/tools/inventory.py` (same file)
- **Dependencies**: ✅ All met
- **Issue**: https://github.com/dougborg/katana-openapi-client/issues/37
- **Spec**: See issue body for complete implementation code

**Key Points**:

- Add to same `tools/inventory.py` file as #35, #36
- Thin wrapper around `client.products.search()`
- Pydantic models: `SearchProductsRequest`, `ProductInfo`, `SearchProductsResponse`
- Handles optional fields safely

**Coordination**: Same file coordination as Agent 2.

______________________________________________________________________

## Batch 2: Integration Tests (AFTER Batch 1)

### Agent 4: Issue #64 - Integration tests

- **Status**: Blocked by #35, #36, #37
- **Estimate**: 2-3 hours
- **File**: `katana_mcp_server/tests/tools/test_inventory.py`
- **Dependencies**: ⏳ Waiting for Batch 1 to complete
- **Issue**: https://github.com/dougborg/katana-openapi-client/issues/64

**Key Points**:

- Unit tests with mocks for all 3 tools
- Integration tests with real API (skip if no KATANA_API_KEY)
- 80%+ test coverage
- Error handling tests

**Start When**: All PRs from Batch 1 are merged

______________________________________________________________________

## Batch 3: Documentation (AFTER Batch 2)

### Agent 5: Issue #65 - Usage documentation

- **Status**: Blocked by #64
- **Estimate**: 2 hours
- **File**: `katana_mcp_server/README.md`
- **Dependencies**: ⏳ Waiting for #64 (tests must pass)
- **Issue**: https://github.com/dougborg/katana-openapi-client/issues/65

**Key Points**:

- Complete README with installation, configuration, usage
- Document all 3 tools with examples
- Claude Desktop integration guide
- Troubleshooting section

**Start When**: PR #64 is merged and tests are passing

______________________________________________________________________

## Batch 4: Packaging & Deployment (AFTER Batch 3)

### Agent 6: Issue #63 - Package and deploy to PyPI

- **Status**: Blocked by #65
- **Estimate**: 3-4 hours
- **Files**:
  - `katana_mcp_server/pyproject.toml` (version bump)
  - `.github/workflows/release-mcp.yml` (new workflow)
- **Dependencies**: ⏳ Waiting for #65 (docs must be complete)
- **Issue**: https://github.com/dougborg/katana-openapi-client/issues/63

**Key Points**:

- Update version to `0.1.0a1`
- Verify dependencies
- Test local build
- Set up PyPI trusted publisher
- Create release workflow
- Publish to PyPI

**Start When**: PR #65 is merged

______________________________________________________________________

## Coordination Strategy

### File Conflicts (Batch 1)

All 3 Batch 1 issues modify the same file (`tools/inventory.py`). Options:

**Option A: Sequential Merges**

1. Agent 1 creates file and implements `check_inventory`
1. Agent 2 adds `list_low_stock_items` to existing file
1. Agent 3 adds `search_products` to existing file

**Option B: Single PR with Multiple Commits**

1. All 3 agents work on separate branches
1. Manually merge into single PR with 3 commits
1. Review and merge together

**Option C: One Agent Does All 3**

1. Assign #35, #36, #37 to single agent
1. Implement all in one PR
1. Faster but less parallelism

**Recommendation**: **Option C** - Less coordination overhead, single PR, cleaner
result.

### Progress Tracking

Track progress via issue comments and PR links:

- [ ] #35 - check_inventory (Agent: \_\_\_\_\_\_)
- [ ] #36 - list_low_stock_items (Agent: \_\_\_\_\_\_)
- [ ] #37 - search_products (Agent: \_\_\_\_\_\_)
- [ ] #64 - Integration tests (Agent: \_\_\_\_\_\_)
- [ ] #65 - Documentation (Agent: \_\_\_\_\_\_)
- [ ] #63 - Package and deploy (Agent: \_\_\_\_\_\_)

______________________________________________________________________

## Reference Documentation

- **Implementation Details**: [TALL_THIN_MAN_PLAN.md](./TALL_THIN_MAN_PLAN.md)
- **Architecture**: [ADR-010: Katana MCP Server](../adr/0010-katana-mcp-server.md)
- **Domain Helpers**:
  [katana_public_api_client/helpers/](../../katana_public_api_client/helpers/)
- **Existing Server**:
  [katana_mcp_server/src/katana_mcp/server.py](../../katana_mcp_server/src/katana_mcp/server.py)

______________________________________________________________________

## Success Criteria

After all batches complete:

- ✅ MCP server has 3 working inventory tools
- ✅ All tools tested (unit + integration)
- ✅ Complete documentation
- ✅ Published to PyPI as `katana-mcp-server==0.1.0a1`
- ✅ Can be installed and used with Claude Desktop
- ✅ Ready for user testing and feedback

______________________________________________________________________

## Next Steps After Alpha

After v0.1.0-alpha is deployed:

1. Gather user feedback
1. Fix any issues found in alpha testing
1. Implement Phase 2: Sales Order helpers + tools (#38-40)
1. Implement Phase 3: Purchase Order helpers + tools (#41-43)
1. Implement Phase 4: Manufacturing Order helpers + tools (#44-46)
1. Release v0.1.0 final with all 12 tools
