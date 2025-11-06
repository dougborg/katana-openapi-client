______________________________________________________________________

## description: 'Update documentation after code changes following project standards'

# Update Documentation

Update project documentation after code changes to keep docs in sync with
implementation.

## Instructions

1. **Identify documentation needs** based on changes:

   - **User-facing changes**: README, guides, cookbook
   - **Developer changes**: CONTRIBUTING, CLAUDE.md, AGENT_WORKFLOW.md
   - **Architectural changes**: New ADR or update existing
   - **API changes**: Docstrings, API reference
   - **Process changes**: Workflow guides

1. **Update affected documentation**:

   **For new features**:

   - Add docstrings to all public functions/classes
   - Update README if user-facing
   - Add cookbook example
   - Update relevant guides

   **For API changes**:

   - Update docstrings
   - Regenerate API docs if needed
   - Update examples in guides

   **For architectural decisions**:

   - Create new ADR using `create-adr.prompt.md`
   - Update related ADRs if superseded
   - Update `docs/adr/README.md` index

   **For breaking changes**:

   - Document in CHANGELOG
   - Create migration guide
   - Add deprecation warnings
   - Update all examples

1. **Format documentation**:

   ```bash
   uv run poe format
   ```

1. **Validate changes**:

   ```bash
   # Check formatting
   uv run poe format-check

   # Build docs (takes ~2.5 minutes)
   uv run poe docs-build

   # Serve locally to review
   uv run poe docs-serve  # http://localhost:8000
   ```

1. **Test all code examples**:

   - Copy examples to test file
   - Run in project environment
   - Verify output matches docs
   - Test error cases if documented

1. **Verify all links work**:

   - Internal links to other docs
   - Links to code files
   - External links (API docs, GitHub)
   - Anchor links within documents

1. **Update navigation** if needed:

   - `mkdocs.yml` for new pages
   - README links for major docs
   - `docs/adr/README.md` for new ADRs

## Documentation Files to Consider

### Main Documentation

- `README.md` - Project overview
- `CLAUDE.md` - Claude Code guide
- `AGENT_WORKFLOW.md` - AI agent workflows
- `.github/copilot-instructions.md` - Copilot instructions

### User Guides

- `docs/KATANA_CLIENT_GUIDE.md` - Client usage
- `docs/COOKBOOK.md` - Common patterns
- `docs/CONTRIBUTING.md` - Contribution guide
- `docs/TESTING_GUIDE.md` - Testing guide

### Developer Docs

- `docs/adr/` - Architecture Decision Records
- `katana_mcp_server/README.md` - MCP server guide
- API docstrings in code

## Docstring Template

```python
def process_order(
    order_id: str,
    confirm: bool = False
) -> str:
    """Process an order with optional confirmation.

    Args:
        order_id: Unique identifier for the order
        confirm: If True, actually process; if False, preview only

    Returns:
        Success message or error description

    Raises:
        ValueError: If order_id is invalid
        HTTPError: If API call fails

    Example:
        >>> # Preview mode
        >>> result = process_order("ORD-123", confirm=False)
        >>> print(result)
        'Preview: Would process order ORD-123'

        >>> # Execute mode
        >>> result = process_order("ORD-123", confirm=True)
        >>> print(result)
        'Processed order ORD-123'
    """
    ...
```

## Cookbook Entry Template

````markdown
## Task: [What User Wants to Do]

**Use case**: [Brief description of when to use this]

### Code Example

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async with KatanaClient() as client:
    # Clear, working example
    response = await get_all_products.asyncio_detailed(
        client=client,
        category="Electronics",
        limit=10
    )

    if response.status_code == 200:
        products = response.parsed.data
        for product in products:
            print(f"{product.name}: {product.price}")
````

### Expected Output

```
Product 1: $99.99
Product 2: $149.99
...
```

### Common Variations

- Filter by multiple categories
- Pagination handling
- Error handling

```

## Success Criteria

- [ ] All affected documentation updated
- [ ] Docstrings added for public APIs
- [ ] Code examples tested and working
- [ ] Links verified (no broken links)
- [ ] Formatting correct (`uv run poe format`)
- [ ] Docs build successfully
- [ ] Navigation updated if needed
- [ ] Migration guide for breaking changes
- [ ] Screenshots updated if UI changed
- [ ] Version numbers current
```
