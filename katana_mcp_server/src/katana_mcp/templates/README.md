# MCP Tool Response Templates

This directory contains markdown templates for formatting MCP tool responses.

## Template System

The template system provides clean separation between business logic and response
formatting. Tools return `ToolResult` objects containing both markdown content (from
templates) and structured JSON data (from Pydantic models).

- **`__init__.py`**: Template loader with `load_template()` and `format_template()`
  functions
- **`*.md` files**: Markdown templates for different response scenarios

## Usage

```python
from fastmcp.tools.tool import ToolResult
from katana_mcp.templates import format_template

# Format template and return dual-format response
markdown = format_template(
    "order_created",
    order_number="PO-2024-001",
    order_id=1234,
    supplier_id=42,
    location_id=1,
    total_cost=2550.00,
    currency="USD",
    created_at="2024-01-15T10:30:00Z",
    status="open",
    line_items_text="- Widget x100 @ $25.50",
    next_steps_text="- Track order status"
)

# Return ToolResult with both formats
return ToolResult(
    content=markdown,                    # Human-readable markdown
    structured_content=response.model_dump()  # Machine-readable JSON
)
```

## Available Templates

### Purchase Orders

- **`order_preview.md`**: Purchase order preview (confirm=false)
- **`order_created.md`**: Order creation success (confirm=true)
- **`order_received.md`**: Receipt confirmation

### Order Verification

- **`order_verification_match.md`**: Perfect match - all items verified
- **`order_verification_partial.md`**: Partial match with discrepancies
- **`order_verification_no_match.md`**: No matches found

### Items

- **`item_search_results.md`**: Search results listing
- **`item_details.md`**: Variant detail view
- **`stock_summary.md`**: Stock level summary

### Order Fulfillment

- **`order_fulfilled.md`**: Manufacturing/sales order fulfillment

### Utility

- **`error.md`**: General error formatting

## Integration Pattern

Each tool module follows this pattern:

1. **Pydantic Response Model** - Defines structured response data
2. **Helper Function** - Converts response to `ToolResult` using templates
3. **Tool Function** - Returns `ToolResult` with dual-format output

Example from `purchase_orders.py`:

```python
def _po_response_to_tool_result(response: PurchaseOrderResponse) -> ToolResult:
    structured_data = response.model_dump()
    template = "order_preview" if response.is_preview else "order_created"
    markdown = format_template(template, **kwargs)
    return ToolResult(content=markdown, structured_content=structured_data)
```

## Type Safety Note

Template format specifiers must match value types:

- Numeric specifiers (e.g., `{total_cost:,.2f}`) require `int` or `float`, not strings
- The `format_template()` function accepts `Any` type but will raise `ValueError` if
  types don't match format specs
- API responses may return stringified numbers - convert with `float()` before passing
  to templates with numeric format specifiers
