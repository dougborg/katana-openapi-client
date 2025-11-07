# MCP Server v0.1.0 Release Checklist

**Target Date**: TBD **Release Manager**: TBD **Status**: 🔴 In Progress

______________________________________________________________________

## Overview

MCP v0.1.0 is the first alpha release showcasing all MCP features (tools, resources,
prompts) with a focused set of Katana inventory and order management primitives.

**Design Philosophy**: "Small set of all MCP features to see how everything works
together"

______________________________________________________________________

## Phase 1: Feature Completeness

### Tools Implementation (10 tools)

#### ✅ Completed Tools

- [x] `search_variants` - Search inventory items
- [x] `check_inventory` - Check stock levels
- [x] `create_purchase_order` - Create POs with elicitation

#### ❌ Missing Tools (Track with issues)

- [ ] `get_variant_details` - Get detailed SKU info (#84)
- [ ] `create_product` - Create new products (#85)
- [ ] `create_material` - Create new materials (#85)
- [ ] `verify_order_document` - Verify PO documents (#86)
- [ ] `receive_purchase_order` - Receive PO shipments (#43)
- [ ] `create_manufacturing_order` - Create manufacturing orders (#44)
- [ ] `fulfill_order` - Complete MO / fulfill SO (#87)

**Status**: 3/10 tools (30%) - 🔴 **BLOCKER**

### Resources Implementation (6 resources)

#### ❌ All Resources Missing (Track with issues)

- [ ] `inventory://items` - List all inventory items (#47)
- [ ] `inventory://stock-movements` - Stock movement history (#47)
- [ ] `inventory://stock-adjustments` - Stock adjustments (#47)
- [ ] `orders://sales-orders` - Sales orders list (#48)
- [ ] `orders://purchase-orders` - Purchase orders list (#48)
- [ ] `orders://manufacturing-orders` - Manufacturing orders list (#48)

**Status**: 0/6 resources (0%) - 🔴 **BLOCKER**

### Prompts Implementation (3 prompts)

#### ❌ All Prompts Missing (Track with issues)

- [ ] `create_and_receive_po` - Complete PO workflow (#50)
- [ ] `verify_and_create_po` - Verify doc & create PO (#50)
- [ ] `fulfill_order` - Complete MO + fulfill SO workflow (#50)

**Status**: 0/3 prompts (0%) - 🔴 **BLOCKER**

______________________________________________________________________

## Phase 2: Testing & Quality

### Unit Tests

- [ ] All tools have comprehensive unit tests
- [ ] All resources have unit tests
- [ ] Error handling tests for all code paths
- [ ] Elicitation pattern tests (confirm=true/false)
- [ ] **Target**: 80%+ test coverage

**Current Coverage**: TBD - Run `uv run poe test-coverage` in `katana_mcp_server/`

### Integration Tests

- [ ] Integration tests for inventory tools (#64 - ALPHA-01)
- [ ] Integration tests for order tools (#52)
- [ ] End-to-end workflow tests (#52)
- [ ] Real Katana API testing (requires `KATANA_API_KEY`)

**Status**: 🔴 **BLOCKER** - No integration tests exist

### Manual Testing Checklist

- [ ] Test with Claude Desktop app
- [ ] Test with Cline VS Code extension
- [ ] Test all 7 user workflows end-to-end
- [ ] Test error handling (network errors, auth failures, validation errors)
- [ ] Test elicitation pattern UX (preview → confirm)
- [ ] Verify resource URIs work in Claude
- [ ] Verify prompts appear in Claude prompt library

______________________________________________________________________

## Phase 3: Documentation

### API Documentation

- [ ] Tool documentation complete (all 10 tools) (#51, #65 - ALPHA-02)
- [ ] Resource documentation complete (all 6 resources) (#51)
- [ ] Prompt documentation complete (all 3 prompts) (#51)
- [ ] Architecture documentation (#51)
- [ ] Development guide (#51)

**Status**: 🔴 **BLOCKER** - Documentation incomplete

### User Documentation

- [ ] Installation guide (#65 - ALPHA-02)
- [ ] Quick start guide (#65 - ALPHA-02)
- [ ] Configuration guide (API key, MCP settings) (#65)
- [ ] Usage examples for all workflows (#53)
- [ ] Troubleshooting guide (#65)

**Status**: 🔴 **BLOCKER** - User docs missing

### Code Quality Documentation

- [ ] All public functions have docstrings
- [ ] All Pydantic models have field descriptions
- [ ] README.md complete with badges
- [ ] CHANGELOG.md generated
- [ ] LICENSE file present

______________________________________________________________________

## Phase 4: Release Infrastructure

### PyPI Publishing (#54)

- [ ] Configure `pyproject.toml` with package metadata
- [ ] Set up PyPI publishing workflow (GitHub Actions)
- [ ] Test publishing to Test PyPI
- [ ] Verify package installs correctly from Test PyPI
- [ ] Configure trusted publisher on PyPI
- [ ] Generate API token for PyPI

**Status**: 🟡 In Progress - See #54

### Docker MCP Registry (#81)

- [ ] Review Docker MCP Registry submission requirements
- [ ] Prepare registry submission materials
- [ ] Submit to Docker MCP Registry
- [ ] Verify listing appears in registry

**Status**: 🔴 Not Started - Blocked by feature completion

### GitHub Release

- [ ] Create release notes from CHANGELOG
- [ ] Tag release: `katana-mcp-server-v0.1.0`
- [ ] Create GitHub release
- [ ] Attach distribution artifacts (wheel, sdist)

______________________________________________________________________

## Phase 5: Pre-Release Verification

### Dependency Check

- [ ] All dependencies up to date
- [ ] No known security vulnerabilities (`uv run pip-audit`)
- [ ] License compatibility verified

### Version Bumping

- [ ] Version updated to `0.1.0` in `pyproject.toml`
- [ ] Version updated in `__init__.py`
- [ ] CHANGELOG.md includes v0.1.0 section

### CI/CD Validation

- [ ] All CI checks passing on main
- [ ] Test suite passing on Python 3.12, 3.13, 3.14
- [ ] Linting passing (ruff)
- [ ] Type checking passing (mypy)
- [ ] Security scans passing (Semgrep, Trivy)

### Package Testing

- [ ] Test wheel installation: `pip install katana-mcp-server-0.1.0-py3-none-any.whl`
- [ ] Test from TestPyPI:
  `pip install --index-url https://test.pypi.org/simple/ katana-mcp-server`
- [ ] Verify MCP server starts: `katana-mcp-server --version`
- [ ] Test in Claude Desktop
- [ ] Test in VS Code with Cline

______________________________________________________________________

## Phase 6: Release Execution

### Pre-Release Communications

- [ ] Draft release announcement
- [ ] Prepare social media posts (Twitter, LinkedIn)
- [ ] Notify stakeholders of release timeline

### Release Steps

1. [ ] Merge all remaining PRs to main
1. [ ] Run final test suite: `uv run poe check`
1. [ ] Create release branch: `release/v0.1.0`
1. [ ] Update version numbers
1. [ ] Generate CHANGELOG
1. [ ] Create release tag: `git tag katana-mcp-server-v0.1.0`
1. [ ] Push tag: `git push origin katana-mcp-server-v0.1.0`
1. [ ] GitHub Actions publishes to PyPI automatically
1. [ ] Verify PyPI listing: https://pypi.org/project/katana-mcp-server/
1. [ ] Create GitHub release with notes
1. [ ] Submit to Docker MCP Registry
1. [ ] Post release announcement

### Post-Release

- [ ] Monitor PyPI download stats
- [ ] Monitor GitHub issues for bug reports
- [ ] Update project README with installation instructions
- [ ] Close milestone: `v0.1.0`
- [ ] Create next milestone: `v0.2.0`

______________________________________________________________________

## Critical Blockers

These MUST be resolved before release:

1. **🔴 Tool Implementation** - Only 3/10 tools complete

   - Missing: get_variant_details, create_product, create_material,
     verify_order_document, receive_purchase_order, create_manufacturing_order,
     fulfill_order
   - **Issues**: #84, #85, #86, #43, #44, #87

1. **🔴 Resource Implementation** - 0/6 resources complete

   - Missing: All inventory and order resources
   - **Issues**: #47, #48

1. **🔴 Prompts Implementation** - 0/3 prompts complete

   - Missing: All workflow prompts
   - **Issue**: #50

1. **🔴 Integration Tests** - No integration tests exist

   - **Issues**: #64 (ALPHA-01), #52

1. **🔴 Documentation** - User docs incomplete

   - **Issues**: #51, #65 (ALPHA-02), #53

1. **🔴 PyPI Publishing** - Infrastructure not set up

   - **Issue**: #54

______________________________________________________________________

## Success Criteria

Release is READY when:

- ✅ All 10 tools implemented and tested
- ✅ All 6 resources implemented and tested
- ✅ All 3 prompts implemented and tested
- ✅ 80%+ test coverage achieved
- ✅ Integration tests passing against real Katana API
- ✅ All documentation complete (API + user docs)
- ✅ PyPI publishing infrastructure working
- ✅ Manual testing complete in Claude Desktop + VS Code
- ✅ All p0-critical and p1-high issues closed

______________________________________________________________________

## Timeline Estimate

Based on remaining work:

- **Tools**: 7 tools × 4-6 hours = 28-42 hours
- **Resources**: 6 resources × 2-3 hours = 12-18 hours
- **Prompts**: 3 prompts × 1-2 hours = 3-6 hours
- **Integration Tests**: 8-12 hours
- **Documentation**: 12-16 hours
- **Release Infrastructure**: 4-6 hours
- **Testing & QA**: 8-12 hours

**Total Estimated Effort**: 75-112 hours (10-14 working days)

______________________________________________________________________

## Related Documentation

- [ADR-010: Katana MCP Server](../../docs/adr/0010-katana-mcp-server.md)
- [Implementation Plan](implementation-plan.md)
- [Architecture Documentation](architecture.md)
- [Development Guide](development.md)

______________________________________________________________________

## Version History

- **2025-01-07**: Initial release checklist created
