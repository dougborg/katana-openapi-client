# Issue Templates

Standard templates for creating well-structured, actionable GitHub issues.

## Standard Issue Structure

```markdown
---
title: [Action verb] [Component] [Specific goal]
labels: [scope:client or scope:mcp], [p1-high, p2-medium, or p3-low], [type]
---

## Background
[Why is this needed? What problem does it solve?]

## Current State
[What exists today? What are the limitations?]

## Proposed Implementation
[How should this be implemented? Include code examples.]

### Key Decisions
- **Decision 1**: [Rationale]
- **Decision 2**: [Rationale]

## Implementation Steps
1. [Specific, actionable step]
2. [Another step]
3. ...

## Testing Strategy
- **Unit Tests**: [Coverage goals]
- **Integration Tests**: [Scenarios]
- **Manual Testing**: [Steps]

## Success Criteria
- ✅ [Measurable outcome]
- ✅ [Another outcome]

## References
- ADR-XXX: [Link]
- Related Issue: #YYY
- Documentation: [Link]

---
**Phase**: [1-4]
**Effort**: [p1-high, p2-medium, p3-low]
**Dependencies**: [Issue numbers or "None"]
**Package**: [client, mcp, or both]
**Agent**: [@agent-name]
```

______________________________________________________________________

## Title Format

### Action Verbs

- **feat**: Add new feature
- **fix**: Fix bug or issue
- **refactor**: Restructure code
- **docs**: Documentation only
- **test**: Add/improve tests
- **perf**: Performance improvement
- **chore**: Maintenance task

### Examples

✅ **Good:**

- `feat(mcp): add inventory search tool`
- `fix(client): handle null values in pagination`
- `refactor(mcp): simplify error handling`
- `docs(client): add domain helper examples`

❌ **Bad:**

- `Add feature` (too vague)
- `Fix bug` (no component)
- `Update code` (no context)

______________________________________________________________________

## Complete Examples

### Example 1: New Feature

````markdown
---
title: feat(mcp): add manufacturing order creation tool
labels: scope:mcp, p2-medium, enhancement
---

## Background

Users need to create manufacturing orders from Claude to trigger production. This
completes the manufacturing workflow started in Phase 1 (list/get operations).

**User workflow:**
1. Check inventory levels
2. Determine production needs
3. Create manufacturing order
4. Track production status

## Current State

- Manufacturing orders can be listed and viewed
- No creation capability exists
- Users must use Katana web UI manually

**Limitations:**
- Breaks agent workflow requiring manual intervention
- Cannot automate production planning

## Proposed Implementation

Add `create_manufacturing_order` tool following the established elicitation pattern:

```python
# katana_mcp_server/src/katana_mcp/tools/manufacturing_orders.py

@mcp.tool()
async def create_manufacturing_order(
    product_id: int,
    quantity: int,
    priority: str = "normal",
    due_date: str | None = None,
    confirm: bool = False,
    ctx: ServerContext = Depends(get_server_context),
) -> str:
    """Create a new manufacturing order.

    Preview with confirm=false (default), execute with confirm=true.
    """
    if not confirm:
        # Preview mode
        return f"Ready to create MO for product {product_id}, qty {quantity}"

    # Actual creation
    async with ctx.katana_client as client:
        response = await create_manufacturing_order_endpoint.asyncio_detailed(
            client=client,
            body=ManufacturingOrderCreate(
                product_id=product_id,
                quantity=quantity,
                priority=priority,
                due_date=due_date,
            ),
        )
        ...
````

### Key Decisions

- **Elicitation Pattern**: Preview/confirm for safety
- **Required Fields**: product_id and quantity only
- **Optional Fields**: priority, due_date, notes
- **Error Handling**: Validate product exists, sufficient materials

## Implementation Steps

1. Add `create_manufacturing_order` function to `manufacturing_orders.py`
1. Implement preview mode (confirm=false)
1. Implement execution mode (confirm=true)
1. Add input validation (product_id exists, quantity > 0)
1. Add error handling for insufficient materials
1. Write unit tests for validation logic
1. Write integration test for full creation workflow
1. Update tool docstring with examples

## Testing Strategy

**Unit Tests:**

- Input validation (invalid product_id, negative quantity)
- Preview mode returns correct summary
- Error messages are clear

**Integration Tests:**

- Create MO with minimal fields
- Create MO with all optional fields
- Handle insufficient materials error
- Verify created MO appears in list

**Manual Testing:**

1. Try preview mode with valid product
1. Confirm and execute creation
1. Verify MO appears in Katana UI
1. Test with invalid product_id
1. Test with insufficient materials

## Success Criteria

- ✅ Tool creates manufacturing orders successfully
- ✅ Preview mode shows accurate summary
- ✅ Validation prevents invalid data
- ✅ Error messages guide user to fix issues
- ✅ Integration test covers happy path
- ✅ Unit tests cover edge cases
- ✅ Docstring includes usage examples

## References

- ADR-010: MCP Server Architecture
- Issue #201: Manufacturing order list/get tools
- `tools/foundation/purchase_orders.py` - Similar pattern

______________________________________________________________________

**Phase**: 2 **Effort**: p2-medium **Dependencies**: Issue #201 **Package**: mcp
**Agent**: @agent-dev

````

---

### Example 2: Bug Fix

```markdown
---
title: fix(client): handle null values in pagination cursor
labels: scope:client, p3-low, bug
---

## Background

Users report `TypeError: 'NoneType' object is not subscriptable` when paginating
through results that end exactly on a page boundary.

**Impact:** Prevents completing pagination of large result sets.

## Current State

Pagination logic assumes `next` cursor always exists:

```python
# Current (broken)
next_url = response.parsed.meta['next']  # Fails if None
````

**Error:**

```
TypeError: 'NoneType' object is not subscriptable
  at katana_client.py:142
```

## Proposed Implementation

Add null check before accessing pagination cursor:

```python
# Fixed
meta = response.parsed.meta
if meta and 'next' in meta and meta['next']:
    next_url = meta['next']
else:
    # End of results
    break
```

### Key Decisions

- **Defensive check**: Verify meta exists, has 'next', and is not None
- **Clear end condition**: Break pagination loop cleanly
- **Logging**: Debug log when pagination completes

## Implementation Steps

1. Add null check in `ResilientAsyncTransport._handle_pagination()`
1. Add test case for last page with no next cursor
1. Add test case for response with no meta
1. Add debug logging for pagination completion
1. Update docstring with pagination end behavior

## Testing Strategy

**Unit Tests:**

- Mock response with `meta.next = None`
- Mock response with no `meta` field
- Verify pagination stops without error

**Integration Tests:**

- Paginate through results ending exactly on page boundary
- Verify all items retrieved
- Verify no errors raised

## Success Criteria

- ✅ No error when pagination ends
- ✅ All results retrieved successfully
- ✅ Test coverage for null cursor
- ✅ Debug logging shows pagination completion

## References

- Related Issue: #145 (pagination errors)
- File: `katana_public_api_client/katana_client.py:142`

______________________________________________________________________

**Phase**: N/A (bug fix) **Effort**: p3-low **Dependencies**: None **Package**: client
**Agent**: @agent-dev

````

---

### Example 3: Refactoring

```markdown
---
title: refactor(mcp): extract common validation logic
labels: scope:mcp, p2-medium, refactor
---

## Background

Multiple MCP tools duplicate validation logic for product IDs, order IDs, and
quantity values. This creates maintenance burden and inconsistent error messages.

**Current duplication:** 8 tools repeat similar validation patterns.

## Current State

Validation duplicated across tools:

```python
# In create_purchase_order
if quantity <= 0:
    raise ValueError("Quantity must be positive")

# In create_sales_order
if quantity <= 0:
    raise ValueError("Quantity must be > 0")  # Slightly different!

# In create_manufacturing_order
if quantity < 1:
    raise ValueError("Quantity must be at least 1")  # Also different!
````

**Problems:**

- Inconsistent error messages
- Code duplication
- Hard to update validation rules

## Proposed Implementation

Create shared validation module:

```python
# katana_mcp_server/src/katana_mcp/validation.py

class ValidationError(Exception):
    """Validation error with user-friendly message."""
    pass

def validate_positive_quantity(quantity: int, field: str = "quantity") -> None:
    """Validate quantity is positive."""
    if quantity <= 0:
        raise ValidationError(f"{field} must be greater than 0, got {quantity}")

def validate_product_exists(
    product_id: int,
    client: KatanaClient,
) -> None:
    """Validate product exists in Katana."""
    # Check product exists
    ...

# Usage in tools
from katana_mcp.validation import validate_positive_quantity

def create_purchase_order(quantity: int, ...):
    validate_positive_quantity(quantity)
    ...
```

### Key Decisions

- **Module location**: `src/katana_mcp/validation.py`
- **Exception type**: Custom `ValidationError` for user-facing errors
- **Async support**: Some validators need async (product exists check)
- **Error messages**: Consistent, helpful format

## Implementation Steps

1. Create `validation.py` module
1. Extract `validate_positive_quantity()`
1. Extract `validate_product_exists()`
1. Extract `validate_order_id()`
1. Update all tools to use validators
1. Write comprehensive validator tests
1. Update tool error handling to catch `ValidationError`
1. Document validation patterns

## Testing Strategy

**Unit Tests:**

- Each validator with valid/invalid inputs
- Error message format consistency
- Edge cases (0, negative, None)

**Integration Tests:**

- Validators work in tool context
- Error messages reach user correctly
- No regression in tool behavior

**Manual Testing:**

- Try invalid inputs in various tools
- Verify consistent error messages
- Check error messages are helpful

## Success Criteria

- ✅ All 8 tools use shared validators
- ✅ Error messages consistent across tools
- ✅ Validator tests cover edge cases
- ✅ No regression in tool functionality
- ✅ Documentation explains validator usage
- ✅ Code duplication eliminated

## References

- Tools affected: `purchase_orders.py`, `sales_orders.py`, `manufacturing_orders.py`,
  `products.py`, `materials.py`, `variants.py`, `stock_adjustments.py`,
  `inventory_items.py`

______________________________________________________________________

**Phase**: 3 (Enhancement) **Effort**: p2-medium **Dependencies**: None (can run
alongside feature work) **Package**: mcp **Agent**: @agent-dev

````

---

## Label Reference

### Scope Labels
- `scope:client` - katana-openapi-client package
- `scope:mcp` - katana-mcp-server package
- `scope:infra` - Infrastructure/monorepo

### Priority Labels
- `p1-high` - 1-2 days, high priority
- `p2-medium` - 4-8 hours, medium priority
- `p3-low` - 1-3 hours, low priority

### Type Labels
- `enhancement` - New feature
- `bug` - Bug fix
- `documentation` - Docs only
- `refactor` - Code improvement
- `testing` - Test improvements
- `dependencies` - Dependency updates

### Status Labels (Optional)
- `blocked` - Cannot proceed
- `in-progress` - Currently being worked
- `needs-review` - Ready for review
- `needs-testing` - Needs manual testing

---

## Creating Issues

### Using GitHub CLI

```bash
# Create from template
gh issue create \
  --title "feat(mcp): add inventory tool" \
  --label "scope:mcp,p2-medium,enhancement" \
  --body "$(cat issue-body.md)"

# Create interactively
gh issue create --web

# Create with assignee
gh issue create \
  --title "fix(client): pagination bug" \
  --label "scope:client,p3-low,bug" \
  --assignee @me \
  --body "Bug description here"
````

### Bulk Creation

For multi-phase plans:

```bash
# create-issues.sh
titles=(
  "feat(mcp): Phase 1 - Foundation"
  "feat(mcp): Phase 2 - Core features"
  "feat(mcp): Phase 3 - Enhancements"
  "feat(mcp): Phase 4 - Documentation"
)

for title in "${titles[@]}"; do
  gh issue create \
    --title "$title" \
    --label "scope:mcp,p2-medium,enhancement" \
    --body-file template.md
done
```

______________________________________________________________________

## Best Practices

### DO ✅

- **Be specific** - Clear, actionable title
- **Provide context** - Explain why this matters
- **Include examples** - Show expected behavior
- **Define success** - Measurable criteria
- **Link references** - ADRs, related issues
- **Assign agents** - Clear ownership
- **Label correctly** - Scope, priority, type

### DON'T ❌

- **Be vague** - "Add feature" isn't helpful
- **Skip background** - Context matters
- **Omit steps** - List specific actions
- **Forget tests** - Always include testing
- **Ignore dependencies** - Document blockers
- **Leave unassigned** - Agent coordination important

______________________________________________________________________

## Summary

**Standard structure:**

1. Background - Why?
1. Current State - What exists?
1. Proposed Implementation - How?
1. Steps - Specific actions
1. Testing - Validation plan
1. Success Criteria - Measurable outcomes
1. References - Related work

**Key elements:**

- Action-oriented title
- Clear scope (labels)
- Specific implementation steps
- Comprehensive testing strategy
- Measurable success criteria
- Proper references

Use these templates to create consistent, actionable issues that enable smooth
execution!
