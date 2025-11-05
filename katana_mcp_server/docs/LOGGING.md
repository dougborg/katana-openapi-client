# Structured Logging in Katana MCP Server

The Katana MCP Server uses structured logging with [structlog](https://www.structlog.org/) to provide rich observability and debugging capabilities.

## Features

- **Structured JSON or text output** - Choose between JSON (for log aggregation) or human-readable text format
- **Contextual information** - Every log includes relevant context (tool names, SKUs, IDs, etc.)
- **Performance metrics** - Automatic duration tracking for all tool executions
- **Trace IDs** - Support for request correlation across operations
- **Security** - Automatic redaction of sensitive data (API keys, passwords, credentials)
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

## Best Practices

1. **Use INFO level in production** - Provides operational visibility without noise
2. **Use DEBUG for troubleshooting** - Includes detailed execution traces
3. **Use JSON format for log aggregation** - Easier to parse and analyze
4. **Use text format for development** - More human-readable
5. **Monitor duration_ms** - Identify performance bottlenecks
6. **Never log sensitive data** - The filter catches common patterns, but be careful with custom fields

## References

- [structlog Documentation](https://www.structlog.org/)
- [Structured Logging Best Practices](https://www.structlog.org/en/stable/why.html)
- [JSON Logging Format](https://www.structlog.org/en/stable/processors.html#structlog.processors.JSONRenderer)
