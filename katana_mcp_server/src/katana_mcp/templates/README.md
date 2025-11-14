# MCP Tool Response Templates

This directory contains markdown templates for formatting MCP tool responses.

## Template System

The template system provides clean separation between business logic and response
formatting:

- **`__init__.py`**: Template loader with `load_template()` and `format_template()`
  functions
- **`*.md` files**: Markdown templates for different response scenarios

## Usage

```python
from katana_mcp.templates import format_template

result = format_template(
    "order_created",
    order_number="PO-2024-001",
    order_id=1234,
    supplier_id=42,
    location_id=1,
    total_cost=2550.00,  # Must be numeric (int/float) for :,.2f format
    currency="USD",
    created_at="2024-01-15T10:30:00Z",
    status="open"
)

# If API returns stringified numbers, convert first:
api_response = {"total": "2550.00"}
result = format_template(
    "order_preview",
    subtotal=float(api_response["total"]),  # Convert string to float
    # ... other fields
)
```

## Available Templates

### Currently Implemented

- **`error.md`**: General error formatting (future use)

### Planned for Future Implementation

These templates are ready but not yet integrated into tool responses:

- **`order_verification_match.md`**: Perfect order verification match
- **`order_verification_partial.md`**: Partial match with discrepancies
- **`order_verification_no_match.md`**: No matches found
- **`order_preview.md`**: Purchase order preview (elicitation pattern)
- **`order_created.md`**: Order creation success confirmation
- **`order_received.md`**: Receipt confirmation

These will be integrated when migrating tools from structured Pydantic responses to
markdown strings per issue #169.

**Note**: The templates are currently NOT integrated into any tools. The tool
implementation in `purchase_orders.py` still returns `VerifyOrderDocumentResponse`
(Pydantic model). Template integration is planned for future work.

## Type Safety Note

Template format specifiers must match value types:

- Numeric specifiers (e.g., `{total_cost:,.2f}`) require `int` or `float`, not strings
- The `format_template()` function accepts `Any` type but will raise `ValueError` if
  types don't match format specs
- API responses may return stringified numbers - convert with `float()` before passing
  to templates with numeric format specifiers
