# ADR-0016: Tool Interface Pattern

## Status

Accepted

Date: 2025-01-11

## Context

MCP tools need consistent, type-safe interfaces for requests and responses. We needed to
decide:

- How to structure tool parameters (flat vs nested)
- How to handle validation
- How to represent responses (structured vs string)
- How to integrate with FastMCP
- How to handle user confirmation for destructive operations

## Decision

We adopt the **Unpack Pattern with Pydantic Models** combined with **FastMCP
Elicitation** for destructive operations.

### Pattern Components

#### 1. Request Models

Pydantic models define tool parameters with full type safety and validation:

```python
class CreatePurchaseOrderRequest(BaseModel):
    """Request to create a purchase order."""
    supplier_id: int = Field(..., description="Supplier ID")
    location_id: int = Field(..., description="Location ID where items will be received")
    order_number: str = Field(..., description="Purchase order number")
    items: list[PurchaseOrderItem] = Field(..., description="Line items", min_length=1)
    confirm: bool = Field(False, description="If false, returns preview. If true, creates order.")
```

#### 2. Unpack Decorator

Flattens nested models for FastMCP compatibility:

```python
@observe_tool
@unpack_pydantic_params
async def create_purchase_order(
    request: Annotated[CreatePurchaseOrderRequest, Unpack()],
    context: Context
) -> PurchaseOrderResponse:
    """Create a new purchase order with user confirmation."""
    ...
```

#### 3. Response Models

Structured responses with success/failure states:

```python
class PurchaseOrderResponse(BaseModel):
    """Response from creating a purchase order."""
    id: int | None = None
    order_number: str
    supplier_id: int
    status: str
    total_cost: float | None = None
    is_preview: bool
    message: str
    warnings: list[str] = []
    next_actions: list[str] = []
```

#### 4. Elicitation Pattern (Safety-Critical Operations)

For destructive operations, we use FastMCP's elicitation to request user confirmation:

```python
# Preview mode (confirm=false) - show what would happen
if not request.confirm:
    return preview_response()

# Request user confirmation via elicitation
elicit_result = await context.elicit(
    f"Create purchase order {order_number} with {item_count} items totaling ${total}?",
    ConfirmationSchema,
)

# Handle user response
if elicit_result.action != "accept":
    return cancelled_response()

if not elicit_result.data.confirm:
    return declined_response()

# User confirmed - proceed with operation
result = await create_order()
return success_response(result)
```

#### 5. Shared Schemas

Common schemas are extracted to `katana_mcp/tools/schemas.py` to avoid duplication:

```python
# katana_mcp/tools/schemas.py
class ConfirmationSchema(BaseModel):
    """Schema for user confirmation elicitation."""
    confirm: bool = Field(..., description="True to proceed, False to cancel")
```

### Benefits

- **Type Safety**: Pydantic validates all inputs at runtime
- **Documentation**: Model fields are self-documenting with descriptions
- **IDE Support**: Autocomplete and type checking work perfectly
- **Testability**: Easy to mock and test with Pydantic models
- **Consistency**: All tools follow the same pattern
- **Safety**: Destructive operations require explicit user confirmation
- **DRY**: Shared schemas eliminate duplication

## Consequences

### Positive

- Type-safe tool interfaces prevent runtime errors
- Self-documenting parameters improve developer experience
- Validation errors are clear and actionable
- Easy to add new parameters (just update model)
- Elicitation prevents accidental destructive operations
- Shared schemas ensure consistency across tools

### Negative

- More boilerplate (request/response models for each tool)
- Unpack decorator adds complexity
- Learning curve for new contributors
- Elicitation adds extra step for confirmed operations

### Neutral

- Models live in same file as tool implementation
- Each tool has 2-3 model classes (Request, Response, nested types)
- Elicitation pattern only used for destructive operations

## Alternatives Considered

### Alternative 1: Flat Parameters

```python
async def create_purchase_order(
    supplier_id: int,
    location_id: int,
    order_number: str,
    items: list[dict],  # ❌ Not type-safe
    context: Context
) -> dict:
    ...
```

**Why rejected**: No validation, not type-safe, hard to document nested structures

### Alternative 2: Dictionary-Based

```python
async def create_purchase_order(
    params: dict,  # ❌ No type safety
    context: Context
) -> dict:
    ...
```

**Why rejected**: No IDE support, no validation, no documentation

### Alternative 3: Manual Confirmation via Response Field

```python
# Return a "pending" response, require second call to confirm
async def create_purchase_order(...) -> dict:
    if not confirmed:
        return {"status": "pending", "confirmation_required": True}
    # Otherwise create
```

**Why rejected**: Two API calls required, harder to use, no built-in UI support

## Implementation Examples

Tools using this pattern:

- `create_purchase_order` - Preview/confirm with elicitation
- `receive_purchase_order` - Preview/confirm with elicitation
- `create_manufacturing_order` - Preview/confirm with elicitation
- `fulfill_order` - Preview/confirm with elicitation
- `verify_order_document` - Read-only, no elicitation needed
- `search_items` - Read-only, no elicitation needed

## References

- [ADR-0011: Pydantic Domain Models](../../katana_public_api_client/docs/adr/0011-pydantic-domain-models.md)
- [ADR-0017: Automated Tool Documentation](0017-automated-tool-documentation.md)
- [katana_mcp/unpack.py](../../src/katana_mcp/unpack.py) - Unpack decorator
  implementation
- [katana_mcp/tools/schemas.py](../../src/katana_mcp/tools/schemas.py) - Shared
  confirmation schema
- [FastMCP Documentation](https://github.com/jlowin/fastmcp) - Elicitation pattern
- [PR #173](https://github.com/dougborg/katana-openapi-client/pull/173) - Elicitation
  implementation
