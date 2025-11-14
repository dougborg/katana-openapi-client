# ADR-0017: Automated Tool Documentation

## Status

Accepted

Date: 2025-01-11

## Context

MCP tools need comprehensive documentation for both human developers and AI agents.
Documentation must be:

- **Accurate**: Synchronized with implementation
- **Complete**: Covers all tools and parameters
- **Discoverable**: Easy to find and use
- **Multi-format**: Serves different audiences (humans, agents, APIs)
- **Maintainable**: Doesn't get out of sync with code

The challenge is balancing completeness with maintainability while serving multiple
audiences.

## Decision

We adopt a **multi-layered documentation approach** where code serves as the single
source of truth, with automated extraction for discovery and reference documentation.

### Documentation Layers

#### Layer 1: Python Docstrings (Primary Source of Truth)

Every tool has a comprehensive Google-style docstring:

```python
@observe_tool
@unpack_pydantic_params
async def create_purchase_order(
    request: Annotated[CreatePurchaseOrderRequest, Unpack()],
    context: Context
) -> PurchaseOrderResponse:
    """Create a new purchase order with user confirmation.

    🔴 HIGH-RISK OPERATION: Creates financial commitment. User confirmation required.

    This tool uses FastMCP elicitation to show a preview before creating the order.
    The user must explicitly confirm before the purchase order is created.

    **Workflow**:
    1. Tool receives request parameters
    2. Validates supplier and location exist
    3. Calculates totals and shows preview
    4. Requests user confirmation via elicitation
    5. Creates order if confirmed

    **Related Tools**:
    - `receive_purchase_order` - Receive delivered items
    - `verify_order_document` - Validate supplier invoice

    **Related Resources**:
    - `katana://purchase-orders` - View all purchase orders

    Args:
        request: Purchase order creation request with supplier, items, etc.
        context: FastMCP context for services and elicitation

    Returns:
        PurchaseOrderResponse with success status and order details

    Raises:
        ValidationError: If parameters are invalid
        APIError: If Katana API call fails

    Example:
        Request: {
            "supplier_id": 4001,
            "location_id": 1,
            "order_number": "PO-2024-001",
            "items": [
                {"variant_id": 501, "quantity": 100, "price_per_unit": 25.50}
            ],
            "confirm": false  # Preview mode
        }
        Returns: Preview showing order details and total
    """
```

**Required Elements**:

- One-line summary
- Risk indicator for destructive operations (🔴/🟡/🟢)
- Workflow description
- Related tools/resources
- Full Args/Returns/Raises documentation
- At least one example

#### Layer 2: Pydantic Field Descriptions

Model fields include rich descriptions that become part of the API schema:

```python
class CreatePurchaseOrderRequest(BaseModel):
    """Request to create a purchase order."""

    supplier_id: int = Field(..., description="Supplier ID from Katana")
    location_id: int = Field(..., description="Warehouse location ID where items will be received")
    order_number: str = Field(..., description="Unique PO number (e.g., PO-2025-001)")
    items: list[PurchaseOrderItem] = Field(
        ...,
        description="Items to purchase with quantities and prices",
        min_length=1
    )
    confirm: bool = Field(
        False,
        description="If false, returns preview. If true, creates order after user confirmation."
    )
```

**Requirements**:

- Every field must have a `description`
- Descriptions should include:
  - What the field represents
  - Expected format/values
  - Constraints or validation rules

#### Layer 3: Observability Decorators

The `@observe_tool` decorator automatically logs tool invocations, providing real-time
documentation of usage patterns:

```python
@observe_tool  # Logs: tool_invoked, tool_completed, tool_failed
@unpack_pydantic_params
async def my_tool(...):
    ...
```

Benefits:

- Automatic timing/performance metrics
- Error tracking
- Usage pattern analysis
- No manual logging code needed

#### Layer 4: Tool Metadata Generator (Pending)

**Status**: Implementation pending in
[PR #170](https://github.com/dougborg/katana-openapi-client/pull/170)

`scripts/generate_tools_json.py` will auto-generate MCP tool metadata for discovery and
Docker registry:

```python
# Will extract:
# - Tool names from function definitions
# - Descriptions from first line of docstrings
# - Parameters from Pydantic models (via AST parsing)

$ python scripts/generate_tools_json.py -o tools.json --pretty
```

**Output**: `tools.json` for Docker MCP Registry submission

#### Layer 5: Template-Based Responses (Optional, Pending)

**Status**: Implementation pending in
[PR #169](https://github.com/dougborg/katana-openapi-client/pull/169)

For tools with complex multi-format responses, externalized markdown templates will
provide consistent formatting:

```python
# Future API (pending PR #169):
from katana_mcp.templates import format_template

result = format_template(
    "order_verification_match",
    order_number="PO-2024-001",
    total_matches=15,
    ...
)
```

Templates will live in `katana_mcp_server/src/katana_mcp/templates/*.md`

### Documentation Standards

**Docstring Style**: Google Style (matches Python ecosystem conventions)

**Field Descriptions**: Complete sentences with punctuation

**Examples**: Real-world request/response pairs in docstrings

**Cross-References**: Link to related tools, resources, and ADRs

## Consequences

### Positive

- **Always Accurate**: Code is documentation - can't get out of sync
- **Comprehensive**: Multiple layers serve different needs
- **Discoverable**: Tools are self-documenting via metadata
- **IDE Support**: Docstrings and type hints provide rich IDE experience
- **Agent-Friendly**: AI agents can understand tool capabilities from metadata
- **Maintainable**: Single source of truth reduces duplication

### Negative

- **Verbose Docstrings**: Required detail makes functions longer
- **Upfront Work**: Each tool requires comprehensive documentation
- **Template Maintenance**: External templates need manual updates (if used)
- **Generator Maintenance**: `generate_tools_json.py` must track code changes

### Neutral

- **Convention Over Configuration**: Strict standards reduce flexibility but increase
  consistency
- **Documentation Review**: PRs require documentation review alongside code review
- **Template Opt-In**: Templates are optional for tools with complex responses

## Documentation Workflow

### Adding a New Tool

1. Write comprehensive docstring following Layer 1 standards
1. Add field descriptions to all Pydantic models (Layer 2)
1. Apply `@observe_tool` decorator (Layer 3)
1. (Future) Run `scripts/generate_tools_json.py` to update metadata (Layer 4, pending PR
   #170)
1. (Optional, Future) Create response template if needed (Layer 5, pending PR #169)

### Maintaining Documentation

- **Code Changes**: Update docstrings and field descriptions
- **Examples**: Keep example requests/responses current with API
- **Metadata**: (Future) Regenerate `tools.json` before each release (once PR #170 is
  merged)
- **Templates**: (Future) Update templates when response format changes (once PR #169 is
  merged)

## Alternatives Considered

### Alternative 1: External Documentation Only

Keep comprehensive docs in separate markdown files, minimal docstrings in code.

**Why rejected**:

- Gets out of sync quickly
- Harder to maintain
- Reduces IDE support
- Harder for agents to discover

### Alternative 2: Minimal Docstrings

Brief one-line docstrings, detailed docs maintained separately.

**Why rejected**:

- Reduces discoverability
- IDE doesn't show full context
- Agents can't understand tool capabilities
- Requires context switching to understand tools

### Alternative 3: Auto-Generated from OpenAPI

Generate all MCP documentation from OpenAPI spec.

**Why rejected**:

- MCP tools don't map 1:1 to API endpoints
- MCP tools provide higher-level workflows
- Would lose tool-specific context and examples
- OpenAPI spec doesn't capture elicitation patterns

### Alternative 4: Template-First Approach

Require templates for all tool responses.

**Why rejected**:

- Overkill for simple responses
- More files to maintain
- Templates needed only for complex multi-format responses
- Pydantic models already provide structure

## Implementation Status

**Fully Implemented**:

- Layer 1: Comprehensive docstrings on all tools ✅
- Layer 2: Field descriptions on all Pydantic models ✅
- Layer 3: `@observe_tool` decorator on all tools ✅

**Pending Implementation**:

- Layer 4: `scripts/generate_tools_json.py` generator (see
  [PR #170](https://github.com/dougborg/katana-openapi-client/pull/170))
- Layer 5: Templates for tool responses (see
  [PR #169](https://github.com/dougborg/katana-openapi-client/pull/169))

**Documentation Coverage**:

- 15 foundation tools documented
- All request/response models documented
- Cross-references added to related tools/resources

## Tools Documentation Examples

**Read-Only Tool** (`search_items`):

- 🟢 indicator (safe, no confirmation needed)
- Example request/response
- Related tools and resources
- Performance characteristics

**Destructive Tool** (`create_purchase_order`):

- 🔴 indicator (requires confirmation)
- Elicitation workflow documented
- Preview vs confirm modes explained
- Safety patterns highlighted

**Verification Tool** (`verify_order_document`):

- 🟡 indicator (reads multiple resources)
- Template-based response format
- Discrepancy handling documented
- Suggested actions explained

## References

- [ADR-0016: Tool Interface Pattern](0016-tool-interface-pattern.md)
- [ADR-004: Defer Observability to httpx](../../katana_public_api_client/docs/adr/0004-defer-observability-to-httpx.md)
- [katana_mcp/logging.py](../../src/katana_mcp/logging.py) - Observability decorators
- [Google Style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [PR #167](https://github.com/dougborg/katana-openapi-client/pull/167) - Observability
  decorators
- [PR #169](https://github.com/dougborg/katana-openapi-client/pull/169) - Template
  externalization (pending)
- [PR #170](https://github.com/dougborg/katana-openapi-client/pull/170) - Tools.json
  generator (pending)
