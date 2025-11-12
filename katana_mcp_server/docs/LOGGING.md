# Structured Logging in Katana MCP Server

The Katana MCP Server uses structured logging with
[structlog](https://www.structlog.org/) to provide rich observability and debugging
capabilities.

## Features

- **Structured JSON or text output** - Choose between JSON (for log aggregation) or
  human-readable text format
- **Contextual information** - Every log includes relevant context (tool names, SKUs,
  IDs, etc.)
- **Performance metrics** - Automatic duration tracking for all tool executions
- **Trace IDs** - Support for request correlation across operations
- **Security** - Automatic redaction of sensitive data (API keys, passwords,
  credentials)
- **Configurable levels** - Control log verbosity via environment variables

## Configuration

### Environment Variables

Configure logging behavior with these environment variables:

- **`KATANA_MCP_LOG_LEVEL`** - Log level (default: `INFO`)

  - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`

- **`KATANA_MCP_LOG_FORMAT`** - Output format (default: `json`)

  - Options: `json`, `text`

### Examples

**Development (verbose text output):**

```bash
export KATANA_MCP_LOG_LEVEL=DEBUG
export KATANA_MCP_LOG_FORMAT=text
katana-mcp-server
```

**Production (structured JSON):**

```bash
export KATANA_MCP_LOG_LEVEL=INFO
export KATANA_MCP_LOG_FORMAT=json
katana-mcp-server
```

## Log Structure

### JSON Format Example

```json
{
  "event": "tool_executed",
  "tool_name": "search_items",
  "query": "widget",
  "result_count": 15,
  "duration_ms": 245.67,
  "timestamp": "2025-01-05T17:08:40.123456Z",
  "level": "info"
}
```

### Text Format Example

```
2025-01-05 17:08:40 [info     ] tool_executed         tool_name=search_items query=widget result_count=15 duration_ms=245.67
```

## Logged Events

### Server Lifecycle

**Server Initialization:**

```json
{
  "event": "server_initializing",
  "version": "0.4.0",
  "base_url": "https://api.katanamrp.com/v1",
  "level": "info"
}
```

**Client Ready:**

```json
{
  "event": "client_initialized",
  "timeout": 30.0,
  "max_retries": 5,
  "max_pages": 100,
  "level": "info"
}
```

**Server Ready:**

```json
{
  "event": "server_ready",
  "version": "0.4.0",
  "level": "info"
}
```

### Tool Execution

**Inventory Check (Success):**

```json
{
  "event": "inventory_check_completed",
  "sku": "WIDGET-001",
  "product_name": "Widget Pro",
  "available_stock": 100,
  "committed": 30,
  "duration_ms": 123.45,
  "level": "info"
}
```

**Search Items (Success):**

```json
{
  "event": "item_search_completed",
  "query": "widget",
  "result_count": 15,
  "duration_ms": 245.67,
  "level": "info"
}
```

**Create Item (Success):**

```json
{
  "event": "item_create_completed",
  "item_type": "product",
  "item_id": 123,
  "name": "Widget Pro",
  "sku": "WGT-PRO-001",
  "duration_ms": 567.89,
  "level": "info"
}
```

### Error Logging

**Tool Failure:**

```json
{
  "event": "item_search_failed",
  "query": "invalid",
  "error": "Invalid search query",
  "error_type": "ValueError",
  "duration_ms": 12.34,
  "level": "error",
  "exception": "Traceback (most recent call last)..."
}
```

**Authentication Error:**

```json
{
  "event": "authentication_failed",
  "reason": "KATANA_API_KEY environment variable is required",
  "message": "Please set it in your .env file or environment.",
  "level": "error"
}
```

## Security Features

### Sensitive Data Redaction

The logger automatically redacts sensitive information from logs:

**Input:**

```python
logger.info("api_call", api_key="secret-key-123", username="john")
```

**Output (JSON):**

```json
{
  "event": "api_call",
  "api_key": "***REDACTED***",
  "username": "john",
  "level": "info"
}
```

**Redacted Keys:**

- `api_key`, `API_KEY`
- `password`, `PASSWORD`
- `secret`, `SECRET`
- `token`, `TOKEN`
- `auth`, `authorization`, `AUTHORIZATION`
- `credential`, `CREDENTIAL`

Any field containing these keywords (case-insensitive) will be automatically redacted.

## Performance Metrics

All tool executions include performance metrics:

- **`duration_ms`** - Time taken to execute the tool (in milliseconds)
- **`result_count`** - Number of items returned (for search/list operations)
- **`threshold`** - Configured threshold (for low stock checks)

Example with metrics:

```json
{
  "event": "low_stock_search_completed",
  "threshold": 10,
  "total_count": 25,
  "returned_count": 25,
  "duration_ms": 678.90,
  "level": "info"
}
```

## Observability Decorators

The Katana MCP Server provides convenience decorators to automatically instrument tools
and service methods with logging, timing, and error tracking.

### @observe_tool

Automatically instruments MCP tool functions with comprehensive observability.

**Features:**

- Automatic logging of tool invocations with parameters
- Execution timing in milliseconds
- Success/failure tracking
- Error details with exception types
- Context parameter filtering (ctx/context excluded from logs)

**Usage:**

```python
from katana_mcp.logging import observe_tool
from fastmcp import Context

@observe_tool
@mcp.tool()
async def my_tool(request: MyRequest, context: Context) -> MyResponse:
    """My tool implementation."""
    return await do_work()
```

**Log Events Produced:**

Tool invocation (INFO level):

```json
{
  "event": "tool_invoked",
  "tool_name": "my_tool",
  "params": {"request": {...}},
  "timestamp": "2025-01-05T17:08:40.123456Z",
  "level": "info"
}
```

Successful completion (INFO level):

```json
{
  "event": "tool_completed",
  "tool_name": "my_tool",
  "duration_ms": 245.67,
  "success": true,
  "timestamp": "2025-01-05T17:08:40.369126Z",
  "level": "info"
}
```

Tool failure (ERROR level):

```json
{
  "event": "tool_failed",
  "tool_name": "my_tool",
  "duration_ms": 12.34,
  "error": "Invalid request parameters",
  "error_type": "ValueError",
  "success": false,
  "timestamp": "2025-01-05T17:08:40.135796Z",
  "level": "error"
}
```

**Best Practices:**

- Place `@observe_tool` before `@mcp.tool()` decorator
- Use with `@unpack_pydantic_params` for parameter unpacking
- Context parameters (ctx, context) are automatically filtered from logs
- No need to add manual timing or error logging in tool implementation

**Example with Parameter Unpacking:**

```python
@observe_tool
@unpack_pydantic_params
async def search_items(
    request: Annotated[SearchItemsRequest, Unpack()], context: Context
) -> SearchItemsResponse:
    """Search for items - automatically instrumented."""
    services = get_services(context)
    return await services.client.variants.search(request.query)
```

### @observe_service

Instruments service layer methods with debug-level logging.

**Features:**

- Service operation tracking
- Method timing
- Error logging with context
- Class name extraction

**Usage:**

```python
from katana_mcp.logging import observe_service

class MyService:
    @observe_service("get_item")
    async def get(self, item_id: int) -> Item:
        """Fetch item by ID."""
        return await self._fetch(item_id)
    
    @observe_service("create_item")
    async def create(self, data: dict) -> Item:
        """Create new item."""
        return await self._create(data)
```

**Log Events Produced:**

Operation started (DEBUG level):

```json
{
  "event": "service_operation_started",
  "service": "MyService",
  "operation": "get_item",
  "params": {"item_id": 123},
  "timestamp": "2025-01-05T17:08:40.123456Z",
  "level": "debug"
}
```

Operation completed (DEBUG level):

```json
{
  "event": "service_operation_completed",
  "service": "MyService",
  "operation": "get_item",
  "duration_ms": 45.67,
  "success": true,
  "timestamp": "2025-01-05T17:08:40.169126Z",
  "level": "debug"
}
```

Operation failed (ERROR level):

```json
{
  "event": "service_operation_failed",
  "service": "MyService",
  "operation": "get_item",
  "duration_ms": 12.34,
  "error": "Item not found",
  "error_type": "ItemNotFoundError",
  "success": false,
  "timestamp": "2025-01-05T17:08:40.135796Z",
  "level": "error"
}
```

**Best Practices:**

- Use descriptive operation names (e.g., "get_product", "create_order")
- Service operations log at DEBUG level (less verbose than tools)
- Use for lower-level operations called by tools
- Provides granular visibility into service layer performance

### Decorator Comparison

| Feature                 | @observe_tool                      | @observe_service                      |
| ----------------------- | ---------------------------------- | ------------------------------------- |
| **Use Case**            | MCP tools (user-facing operations) | Service methods (internal operations) |
| **Log Level**           | INFO                               | DEBUG                                 |
| **Parameter Filtering** | Yes (ctx/context)                  | No                                    |
| **Primary Audience**    | Operations/users                   | Developers                            |
| **Visibility**          | High (always logged in production) | Low (only in debug mode)              |

### Migration Guide

**Before (Manual Logging):**

```python
@mcp.tool()
async def my_tool(request: MyRequest, context: Context) -> MyResponse:
    logger.info("my_tool_started", request=request)
    start_time = time.monotonic()
    try:
        result = await do_work()
        duration_ms = (time.monotonic() - start_time) * 1000
        logger.info("my_tool_completed", duration_ms=duration_ms)
        return result
    except Exception as e:
        logger.error("my_tool_failed", error=str(e))
        raise
```

**After (With Decorator):**

```python
@observe_tool
@mcp.tool()
async def my_tool(request: MyRequest, context: Context) -> MyResponse:
    return await do_work()  # Automatic logging, timing, error tracking!
```

**Benefits:**

- 10+ lines of boilerplate eliminated per tool
- Consistent log format across all tools
- Automatic error tracking without try/except
- Performance metrics captured automatically
- No risk of forgetting to log important events

## Best Practices

1. **Use INFO level in production** - Provides operational visibility without noise
1. **Use DEBUG for troubleshooting** - Includes detailed execution traces and service
   operations
1. **Use JSON format for log aggregation** - Easier to parse and analyze
1. **Use text format for development** - More human-readable
1. **Monitor duration_ms** - Identify performance bottlenecks
1. **Never log sensitive data** - The filter catches common patterns, but be careful
   with custom fields
1. **Use @observe_tool for all MCP tools** - Automatic instrumentation with zero
   boilerplate
1. **Use @observe_service for service methods** - Granular visibility into internal
   operations

## References

- [structlog Documentation](https://www.structlog.org/)
- [Structured Logging Best Practices](https://www.structlog.org/en/stable/why.html)
- [JSON Logging Format](https://www.structlog.org/en/stable/processors.html#structlog.processors.JSONRenderer)
