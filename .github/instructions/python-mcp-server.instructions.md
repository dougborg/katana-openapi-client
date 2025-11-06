______________________________________________________________________

## description: 'Instructions for building Model Context Protocol (MCP) servers using the Python SDK with FastMCP' applyTo: '**/katana_mcp_server/**/\*.py'

# Python MCP Server Development

## Instructions

- Use **uv** for project management: `uv init mcp-server-demo` and `uv add "mcp[cli]"`
- Import FastMCP from `mcp.server.fastmcp`: `from mcp.server.fastmcp import FastMCP`
- Use `@mcp.tool()`, `@mcp.resource()`, and `@mcp.prompt()` decorators for registration
- Type hints are mandatory - they're used for schema generation and validation
- Use Pydantic models, TypedDicts, or dataclasses for structured output
- Tools automatically return structured output when return types are compatible
- For stdio transport, use `mcp.run()` or `mcp.run(transport="stdio")`
- For HTTP servers, use `mcp.run(transport="streamable-http")` or mount to
  Starlette/FastAPI
- Use `Context` parameter in tools/resources to access MCP capabilities: `ctx: Context`
- Send logs with `await ctx.debug()`, `await ctx.info()`, `await ctx.warning()`,
  `await ctx.error()`
- Report progress with `await ctx.report_progress(progress, total, message)`
- Request user input with `await ctx.elicit(message, schema)`
- Use LLM sampling with `await ctx.session.create_message(messages, max_tokens)`
- Configure icons with `Icon(src="path", mimeType="image/png")` for server, tools,
  resources, prompts
- Use `Image` class for automatic image handling:
  `return Image(data=bytes, format="png")`
- Define resource templates with URI patterns: `@mcp.resource("greeting://{name}")`
- Implement completion support by accepting partial values and returning suggestions
- Use lifespan context managers for startup/shutdown with shared resources
- Access lifespan context in tools via `ctx.request_context.lifespan_context`
- For stateless HTTP servers, set `stateless_http=True` in FastMCP initialization
- Enable JSON responses for modern clients: `json_response=True`
- Test servers with: `uv run mcp dev server.py` (Inspector) or
  `uv run mcp install server.py` (Claude Desktop)
- Mount multiple servers in Starlette with different paths:
  `Mount("/path", mcp.streamable_http_app())`
- Configure CORS for browser clients: expose `Mcp-Session-Id` header
- Use low-level Server class for maximum control when FastMCP isn't sufficient

## Katana MCP Server Patterns

### ServerContext Pattern (ADR-010)

- Use `get_services()` to access KatanaClient and other services
- Never instantiate KatanaClient directly in tools
- Leverage shared context for efficiency

```python
from katana_mcp.server import get_services

@mcp.tool()
async def check_inventory(sku: str) -> str:
    """Check inventory for a product SKU."""
    services = get_services()
    # Use services.katana_client for API calls
    response = await get_variant_by_sku.asyncio_detailed(
        client=services.katana_client,
        sku=sku
    )
    return f"Stock level: {response.parsed.stock_on_hand}"
```

### Tool Organization

- **Foundation tools** (`foundation/`) - Basic operations (list, get, search)
- **Workflow tools** (`workflows/`) - Complex multi-step operations

### Preview/Confirm Pattern

- Implement `confirm` parameter for destructive operations
- Preview mode (`confirm=False`): Show what would happen
- Execute mode (`confirm=True`): Actually perform the action

```python
@mcp.tool()
async def delete_order(order_id: str, confirm: bool = False) -> str:
    """Delete an order."""
    if not confirm:
        return f"Preview: Would delete order {order_id}"

    # Actually delete
    services = get_services()
    # ... deletion logic
    return f"Deleted order {order_id}"
```

### Structured Logging

- Use Python logging module
- INFO level for user-facing operations
- DEBUG for internal details
- ERROR for failures

```python
import logging

logger = logging.getLogger(__name__)

@mcp.tool()
async def process_data(data: str) -> str:
    """Process data."""
    logger.info(f"Processing data: {data[:50]}...")
    try:
        result = process(data)
        logger.debug(f"Result: {result}")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise
```

## Best Practices

- Always use type hints - they drive schema generation and validation
- Return Pydantic models or TypedDicts for structured tool outputs
- Keep tool functions focused on single responsibilities
- Provide clear docstrings - they become tool descriptions
- Use descriptive parameter names with type hints
- Validate inputs using Pydantic Field descriptions
- Implement proper error handling with try-except blocks
- Use async functions for I/O-bound operations
- Clean up resources in lifespan context managers
- Log to stderr to avoid interfering with stdio transport (when using stdio)
- Use environment variables for configuration
- Test tools independently before LLM integration
- Consider security when exposing file system or network access
- Use structured output for machine-readable data
- Provide both content and structured data for backward compatibility

## Common Patterns

### Basic Tool with Pydantic Parameters

```python
from pydantic import BaseModel, Field

class SearchParams(BaseModel):
    query: str = Field(description="Search query")
    category: str | None = Field(default=None, description="Optional category filter")

@mcp.tool()
def search_products(params: SearchParams) -> list[dict]:
    """Search for products."""
    services = get_services()
    # Implementation...
    return results
```

### Tool with Context and Progress Reporting

```python
from mcp.server.fastmcp import Context
from mcp.server.session import ServerSession

@mcp.tool()
async def process_orders(
    order_ids: list[str],
    ctx: Context[ServerSession, None]
) -> str:
    """Process multiple orders."""
    total = len(order_ids)

    for i, order_id in enumerate(order_ids):
        await ctx.info(f"Processing order {order_id}")
        await ctx.report_progress(i + 1, total, f"Order {order_id}")

        # Process order...

    return f"Processed {total} orders"
```

### Resource with Dynamic URI

```python
@mcp.resource("products://{sku}")
def get_product_resource(sku: str) -> str:
    """Get product data by SKU."""
    services = get_services()
    # Fetch product data...
    return f"Product data for SKU: {sku}"
```

### Error Handling Pattern

```python
@mcp.tool()
async def risky_operation(input: str) -> str:
    """Operation that might fail."""
    try:
        services = get_services()
        result = await perform_operation(services.katana_client, input)
        return f"Success: {result}"
    except HTTPStatusError as e:
        logger.error(f"API error: {e}")
        return f"API Error: {e.response.status_code}"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"Error: {str(e)}"
```
