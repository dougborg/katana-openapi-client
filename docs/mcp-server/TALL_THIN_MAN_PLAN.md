# Tall Thin Man Plan - MCP Server v0.1.0-alpha

## Overview

Build a complete end-to-end working MCP server with 3 inventory tools, then
incrementally add more functionality. This gets us to a deployable MVP faster while
maintaining quality.

## Architecture

```
┌─────────────────────────────────────────────┐
│  FastMCP Server (server.py)                 │
│  - Lifespan management                      │
│  - KatanaClient initialization              │
│  - Environment-based auth                   │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│  MCP Tools (tools/*.py)                     │
│  - Thin wrappers around domain helpers      │
│  - FastMCP @mcp.tool() decorators           │
│  - Pydantic request/response models         │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│  Domain Helpers (katana_public_api_client)  │
│  - Products, Materials, Variants, etc.      │
│  - Business logic layer                     │
│  - Exception-based error handling           │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│  Generated OpenAPI Client                   │
│  - Raw API endpoints                        │
│  - Transport-layer resilience               │
└─────────────────────────────────────────────┘
```

## Phase 1: Alpha Release (v0.1.0-alpha) - "Tall Thin Man"

**Goal**: Deployable MCP server with 3 working inventory tools

### Issues to Complete

#### Issue #35: Implement check_inventory tool

**File**: `katana_mcp_server/src/katana_mcp/tools/inventory.py` **Estimate**: 2-3 hours

**Implementation**:

```python
from fastmcp import Context
from pydantic import BaseModel, Field

from katana_mcp.server import ServerContext, mcp

class CheckInventoryRequest(BaseModel):
    """Request model for checking inventory."""
    sku: str = Field(..., description="Product SKU to check")

class StockInfo(BaseModel):
    """Stock information for a product."""
    sku: str
    product_name: str
    available_stock: int
    in_production: int
    committed: int

@mcp.tool()
async def check_inventory(
    request: CheckInventoryRequest,
    context: Context[ServerContext]
) -> StockInfo:
    """Check stock levels for a specific product SKU.

    Args:
        request: Request containing SKU to check
        context: Server context with KatanaClient

    Returns:
        StockInfo with current stock levels
    """
    client = context.state.client
    result = await client.inventory.check_stock(request.sku)

    return StockInfo(
        sku=result["sku"],
        product_name=result["name"],
        available_stock=result["available"],
        in_production=result["in_production"],
        committed=result["committed"]
    )
```

**Tests**: `katana_mcp_server/tests/tools/test_inventory.py`

______________________________________________________________________

#### Issue #36: Implement list_low_stock_items tool

**File**: `katana_mcp_server/src/katana_mcp/tools/inventory.py` (same file)
**Estimate**: 2-3 hours

**Implementation**:

```python
class LowStockRequest(BaseModel):
    """Request model for listing low stock items."""
    threshold: int = Field(default=10, description="Stock threshold level")
    limit: int = Field(default=50, description="Maximum items to return")

class LowStockItem(BaseModel):
    """Low stock item information."""
    sku: str
    product_name: str
    current_stock: int
    threshold: int

class LowStockResponse(BaseModel):
    """Response containing low stock items."""
    items: list[LowStockItem]
    total_count: int

@mcp.tool()
async def list_low_stock_items(
    request: LowStockRequest,
    context: Context[ServerContext]
) -> LowStockResponse:
    """List products below stock threshold.

    Args:
        request: Request with threshold and limit
        context: Server context with KatanaClient

    Returns:
        List of products below threshold
    """
    client = context.state.client
    items = await client.inventory.low_stock(threshold=request.threshold)

    # Limit results
    limited_items = items[:request.limit]

    return LowStockResponse(
        items=[
            LowStockItem(
                sku=item["sku"],
                product_name=item["name"],
                current_stock=item["stock"],
                threshold=request.threshold
            )
            for item in limited_items
        ],
        total_count=len(items)
    )
```

______________________________________________________________________

#### Issue #37: Implement search_products tool

**File**: `katana_mcp_server/src/katana_mcp/tools/inventory.py` (same file)
**Estimate**: 2-3 hours

**Implementation**:

```python
class SearchProductsRequest(BaseModel):
    """Request model for searching products."""
    query: str = Field(..., description="Search query (name, SKU, etc.)")
    limit: int = Field(default=20, description="Maximum results to return")

class ProductInfo(BaseModel):
    """Product information."""
    id: int
    sku: str
    name: str
    is_sellable: bool
    stock_level: int | None = None

class SearchProductsResponse(BaseModel):
    """Response containing search results."""
    products: list[ProductInfo]
    total_count: int

@mcp.tool()
async def search_products(
    request: SearchProductsRequest,
    context: Context[ServerContext]
) -> SearchProductsResponse:
    """Search for products by name or SKU.

    Args:
        request: Request with search query and limit
        context: Server context with KatanaClient

    Returns:
        List of matching products
    """
    client = context.state.client
    results = await client.products.search(request.query, limit=request.limit)

    return SearchProductsResponse(
        products=[
            ProductInfo(
                id=product.id,
                sku=product.sku or "",
                name=product.name or "",
                is_sellable=product.is_sellable or False,
                stock_level=getattr(product, 'stock_level', None)
            )
            for product in results
        ],
        total_count=len(results)
    )
```

______________________________________________________________________

#### Issue #64: Add integration tests for MCP inventory tools

**File**: `katana_mcp_server/tests/tools/test_inventory.py` **Estimate**: 2-3 hours

**Implementation**:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

from katana_mcp.tools.inventory import (
    check_inventory,
    list_low_stock_items,
    search_products,
    CheckInventoryRequest,
    LowStockRequest,
    SearchProductsRequest,
)

@pytest.mark.asyncio
async def test_check_inventory():
    """Test check_inventory tool."""
    # Mock context and client
    context = MagicMock()
    context.state.client.inventory.check_stock = AsyncMock(
        return_value={
            "sku": "WIDGET-001",
            "name": "Test Widget",
            "available": 100,
            "in_production": 20,
            "committed": 30
        }
    )

    request = CheckInventoryRequest(sku="WIDGET-001")
    result = await check_inventory(request, context)

    assert result.sku == "WIDGET-001"
    assert result.product_name == "Test Widget"
    assert result.available_stock == 100

@pytest.mark.asyncio
async def test_list_low_stock_items():
    """Test list_low_stock_items tool."""
    # Similar mock structure
    ...

@pytest.mark.asyncio
async def test_search_products():
    """Test search_products tool."""
    # Similar mock structure
    ...

@pytest.mark.integration
@pytest.mark.asyncio
async def test_check_inventory_integration():
    """Integration test with real KatanaClient (requires API key)."""
    # Test with real API calls (skipped if no KATANA_API_KEY)
    ...
```

______________________________________________________________________

#### Issue #65: Create MCP server usage documentation

**File**: `katana_mcp_server/README.md` **Estimate**: 2 hours

**Content**:

````markdown
# Katana MCP Server

Model Context Protocol (MCP) server for Katana Manufacturing ERP.

## Features

- **Inventory Tools**: Check stock, find low stock items, search products
- **Authentication**: Environment-based API key (KATANA_API_KEY)
- **Resilience**: Automatic retries, rate limiting, pagination
- **Type Safety**: Pydantic models for all requests/responses

## Installation

```bash
pip install katana-mcp-server
````

## Configuration

Set your Katana API key:

```bash
export KATANA_API_KEY=your-api-key-here
```

Or create a `.env` file:

```
KATANA_API_KEY=your-api-key-here
KATANA_BASE_URL=https://api.katanamrp.com/v1  # Optional
```

## Usage

### With Claude Desktop

Add to your Claude Desktop config
(`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "katana": {
      "command": "uvx",
      "args": ["katana-mcp-server"],
      "env": {
        "KATANA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Running Standalone

```bash
katana-mcp-server
```

## Available Tools

### check_inventory

Check stock levels for a specific product SKU.

**Parameters**:

- `sku` (string): Product SKU to check

**Example**:

```json
{
  "sku": "WIDGET-001"
}
```

**Returns**:

```json
{
  "sku": "WIDGET-001",
  "product_name": "Widget",
  "available_stock": 100,
  "in_production": 20,
  "committed": 30
}
```

### list_low_stock_items

List products below a stock threshold.

**Parameters**:

- `threshold` (int, default: 10): Stock threshold level
- `limit` (int, default: 50): Maximum items to return

**Returns**: List of low stock items with current levels

### search_products

Search for products by name or SKU.

**Parameters**:

- `query` (string): Search query
- `limit` (int, default: 20): Maximum results

**Returns**: List of matching products with stock info

```

---

#### Issue #63: Package and deploy MCP server v0.1.0-alpha to PyPI
**File**: `katana_mcp_server/pyproject.toml` + CI workflow
**Estimate**: 3-4 hours

**Tasks**:
1. Update `katana_mcp_server/pyproject.toml` version to `0.1.0a1`
2. Ensure dependencies are correct (fastmcp, katana-openapi-client>=0.22.0)
3. Add PyPI publishing workflow for mcp server package
4. Test local build: `cd katana_mcp_server && uv build`
5. Publish to PyPI (requires PyPI trusted publisher setup for katana-mcp-server)

---

## Implementation Order for Agents

### Batch 1: Parallel (3 agents)
- **Agent 1**: Issue #35 - check_inventory tool
- **Agent 2**: Issue #36 - list_low_stock_items tool
- **Agent 3**: Issue #37 - search_products tool

### Batch 2: Sequential
- **After Batch 1**: Issue #64 - Integration tests (needs all 3 tools)
- **After #64**: Issue #65 - Documentation
- **After #65**: Issue #63 - Package and deploy

## Testing Checklist

Before deployment:
- [ ] All 3 tools work independently
- [ ] Integration tests pass
- [ ] Server starts without errors
- [ ] Authentication works with KATANA_API_KEY
- [ ] Can be installed via `pip install katana-mcp-server`
- [ ] Works with Claude Desktop MCP config

## Success Criteria for v0.1.0-alpha

- ✅ Working MCP server with 3 inventory tools
- ✅ Published to PyPI as `katana-mcp-server`
- ✅ Complete usage documentation
- ✅ Integration tests passing
- ✅ Can be used in Claude Desktop

## After Alpha: Phase 2+

Once alpha is deployed and tested:
- Add Sales Order helpers + 3 tools (#38-40)
- Add Purchase Order helpers + 3 tools (#41-43)
- Add Manufacturing Order helpers + 3 tools (#44-46)
- Release v0.1.0 final with all 12 tools
```
