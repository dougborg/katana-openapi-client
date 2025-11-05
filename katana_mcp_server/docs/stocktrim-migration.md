# MCP v0.1.0 - StockTrim Architecture Migration Plan

**Status**: Planning **Goal**: Migrate Katana MCP server to production-ready StockTrim
architecture patterns **Reference**:
[StockTrim MCP Server](https://github.com/dougborg/stocktrim-openapi-client/)

______________________________________________________________________

## Architecture Overview

### Current State (Katana)

```
katana_mcp_server/
├── pyproject.toml
├── src/katana_mcp/
│   ├── server.py          # Basic FastMCP setup
│   ├── tools.py           # Flat tool structure
│   └── models.py          # Request/response models
└── tests/
```

### Target State (StockTrim Pattern)

```
katana_mcp_server/
├── pyproject.toml                    # MCP package config
├── src/katana_mcp_server/
│   ├── __init__.py
│   ├── server.py                     # FastMCP with lifespan management
│   ├── dependencies.py               # DI helpers for context access
│   ├── services/
│   │   ├── __init__.py
│   │   └── base.py                   # BaseService for shared logic
│   ├── tools/
│   │   ├── __init__.py               # register_all_tools()
│   │   ├── foundation/               # Low-level API operations
│   │   │   ├── __init__.py
│   │   │   ├── products.py           # CRUD for products
│   │   │   ├── materials.py          # CRUD for materials
│   │   │   ├── variants.py           # Search, get details
│   │   │   ├── inventory.py          # Stock checks, adjustments
│   │   │   ├── purchase_orders.py    # PO CRUD
│   │   │   ├── manufacturing_orders.py  # MO CRUD
│   │   │   └── sales_orders.py       # SO CRUD
│   │   └── workflows/                # High-level intent operations
│   │       ├── __init__.py
│   │       ├── po_lifecycle.py       # Create + receive PO
│   │       ├── manufacturing.py      # Create + complete MO
│   │       └── document_verification.py  # Verify docs vs POs
│   ├── resources/
│   │   ├── __init__.py               # register_all_resources()
│   │   ├── inventory.py              # Items, movements, adjustments
│   │   └── orders.py                 # Sales, purchase, manufacturing
│   └── prompts/
│       ├── __init__.py               # register_all_prompts()
│       ├── po_workflow.py            # Create + receive workflow
│       ├── verify_document.py        # Document verification
│       └── fulfill_order.py          # Order fulfillment
└── tests/
    ├── conftest.py                   # Mock context fixtures
    ├── test_tools/
    │   ├── test_foundation/
    │   └── test_workflows/
    └── test_resources/
```

______________________________________________________________________

## Key Patterns from StockTrim

### 1. Lifespan Management Pattern

**File**: `server.py`

```python
import os
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator
from fastmcp import FastMCP
from katana_public_api_client import KatanaClient

# Module-level setup
logger = logging.getLogger(__name__)
__version__ = "0.1.0"  # Would typically import from __init__.py

@dataclass
class ServerContext:
    """Container for services available to tools."""
    client: KatanaClient

@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[ServerContext]:
    """
    Manages KatanaClient lifecycle for the MCP server.

    Client is initialized once at startup and shared across all tool calls.
    """
    api_key = os.getenv("KATANA_API_KEY")
    base_url = os.getenv("KATANA_BASE_URL", "https://api.katanamrp.com/v1")

    if not api_key:
        raise ValueError("KATANA_API_KEY environment variable required")

    async with KatanaClient(api_key=api_key, base_url=base_url) as client:
        context = ServerContext(client=client)
        logger.info("KatanaClient initialized")
        yield context
        logger.info("KatanaClient closed")

# Initialize FastMCP with lifespan
mcp = FastMCP(
    name="katana-inventory",
    version=__version__,
    lifespan=lifespan,
    instructions="""
    Katana Manufacturing ERP MCP Server

    This server provides tools for managing inventory, orders, and manufacturing
    in Katana Manufacturing ERP.
    """
)
```

**Benefits**:

- Single client instance shared across all tools
- Proper cleanup on shutdown
- Type-safe context access
- Environment-based configuration

### 2. Tool Registration Pattern

**File**: `tools/foundation/variants.py`

````python
from typing import Literal
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

# 1. Request Model
class SearchVariantsRequest(BaseModel):
    """Search for product variants by name, SKU, or description."""
    query: str = Field(..., description="Search query (name, SKU, description)")
    limit: int = Field(20, ge=1, le=100, description="Max results to return")
    item_type: Literal["all", "product", "material", "service"] = Field(
        "all", description="Filter by item type"
    )

# 2. Response Model
class VariantSearchResult(BaseModel):
    """Single variant in search results."""
    sku: str = Field(..., description="Variant SKU")
    name: str = Field(..., description="Variant name")
    product_name: str | None = Field(None, description="Parent product name")
    item_type: str = Field(..., description="Type: product, material, or service")
    stock_level: float | None = Field(None, description="Current stock quantity")
    in_stock: bool = Field(..., description="Whether item is in stock")

class SearchVariantsResponse(BaseModel):
    """Search results with metadata."""
    items: list[VariantSearchResult]
    total_count: int
    query: str

# 3. Implementation (private)
async def _search_variants_impl(
    request: SearchVariantsRequest,
    context: Context
) -> SearchVariantsResponse:
    """Implementation logic separated for testing."""
    server_context = context.request_context.lifespan_context
    client = server_context.client

    # Search variants using the client's variants helper
    variants = await client.variants.search(
        query=request.query,
        limit=request.limit
    )

    results = [
        VariantSearchResult(
            sku=v.sku,
            name=v.name,
            # ... map fields
        )
        for v in variants
    ]

    return SearchVariantsResponse(
        items=results,
        total_count=len(results),
        query=request.query
    )

# 4. Public Tool (with decorator applied at registration)
async def search_variants(
    request: SearchVariantsRequest,
    context: Context
) -> SearchVariantsResponse:
    """
    Search for product variants across all item types.

    This tool searches products, materials, and services by name, SKU,
    or description. Results include basic info and stock levels.

    **When to use**:
    - Finding items by partial name/SKU
    - Browsing catalog
    - Checking if item exists

    **Use get_variant_details for**:
    - Full BOM information
    - Detailed stock movements
    - Manufacturing parameters

    **Examples**:

    1. Search for widgets:
       ```json
       {"query": "widget", "limit": 10}
       ```

    2. Search only materials:
       ```json
       {"query": "steel", "item_type": "material", "limit": 20}
       ```
    """
    return await _search_variants_impl(request, context)

# 5. Registration Function
def register_tools(mcp: FastMCP) -> None:
    """Register variant tools with the MCP server."""
    mcp.tool()(search_variants)
    mcp.tool()(get_variant_details)
    mcp.tool()(check_inventory)
````

**Benefits**:

- Avoids circular imports (registration happens after all imports)
- Separate `_impl` for unit testing
- Rich Pydantic models with Field descriptions
- Comprehensive docstrings with examples
- Type-safe context access

### 3. Dependencies Helper Pattern

**File**: `dependencies.py`

```python
from dataclasses import dataclass
from fastmcp import Context
from katana_public_api_client import KatanaClient

@dataclass
class Services:
    """Container for services available in tool implementations."""
    client: KatanaClient

def get_services(context: Context) -> Services:
    """
    Extract services from MCP context.

    Usage in tools:
        services = get_services(context)

        # Use existing helpers (variants, products, materials, services, inventory)
        products = await services.client.products.list()

        # For other endpoints (purchase_orders, sales_orders, etc), use generated API:
        from katana_public_api_client.api.purchase_order import create_purchase_order
        po_response = await create_purchase_order.asyncio_detailed(
            client=services.client,
            json_body=...
        )

    Note:
        Only a limited set of helpers currently exist on KatanaClient:
        - variants
        - products
        - materials
        - services
        - inventory

        For other endpoints (purchase_orders, manufacturing_orders, sales_orders),
        you must use the generated API modules directly from katana_public_api_client.api.*
        or implement your own helper methods.
    """
    server_context = context.request_context.lifespan_context
    return Services(client=server_context.client)
```

**Benefits**:

- Single extraction point
- Type-safe service access
- Easy to extend with more services
- Clear dependency injection
- Documents which helpers exist vs need generated API

### 4. Tool Organization: Foundation vs Workflows

#### Foundation Tools (Low-Level)

Granular operations mapping closely to API endpoints:

**File**: `tools/foundation/purchase_orders.py`

```python
# Import generated API methods (no purchase_orders helper exists)
from katana_public_api_client.api.purchase_order import (
    create_purchase_order_asyncio_detailed,
    get_purchase_order_asyncio_detailed,
    receive_purchase_order_asyncio_detailed
)

async def create_purchase_order(
    request: CreatePurchaseOrderRequest,
    context: Context
) -> PurchaseOrderResponse:
    """Create a new purchase order using generated API."""
    services = get_services(context)

    # Use generated API directly (no helper method exists)
    response = await create_purchase_order_asyncio_detailed(
        client=services.client,
        json_body={
            "supplier_id": request.supplier_id,
            "items": request.items,
            "notes": request.notes
        }
    )

    return PurchaseOrderResponse.from_katana(response.parsed)

async def get_purchase_order(
    request: GetPurchaseOrderRequest,
    context: Context
) -> PurchaseOrderResponse:
    """Get purchase order by ID using generated API."""
    services = get_services(context)

    response = await get_purchase_order_asyncio_detailed(
        client=services.client,
        id=request.po_id
    )

    return PurchaseOrderResponse.from_katana(response.parsed)

async def receive_purchase_order(
    request: ReceivePurchaseOrderRequest,
    context: Context
) -> ReceiveResponse:
    """Receive items on a purchase order using generated API."""
    services = get_services(context)

    response = await receive_purchase_order_asyncio_detailed(
        client=services.client,
        id=request.po_id,
        json_body={"items": request.items}
    )

    return ReceiveResponse.from_katana(response.parsed)
```

#### Workflow Tools (High-Level)

Intent-based operations combining multiple foundations:

**File**: `tools/workflows/po_lifecycle.py`

````python
class CreateAndReceivePORequest(BaseModel):
    """Create PO and immediately receive items (for testing/demos)."""
    supplier_id: int
    items: list[OrderItem]
    notes: str | None = None
    auto_receive: bool = Field(
        True,
        description="Automatically receive all items after creation"
    )

class CreateAndReceivePOResponse(BaseModel):
    """Response with both creation and receipt info."""
    purchase_order: PurchaseOrderResponse
    receipt: ReceiveResponse | None
    next_actions: list[str]

async def create_and_receive_po(
    request: CreateAndReceivePORequest,
    context: Context
) -> CreateAndReceivePOResponse:
    """
    Create purchase order and optionally receive items immediately.

    This workflow combines PO creation and receipt in a single operation,
    useful for:
    - Demo scenarios
    - Testing workflows
    - Quick inventory replenishment

    **Steps**:
    1. Create purchase order with supplier and items
    2. If auto_receive=true, receive all items
    3. Return combined results with next actions

    **Example**:
    ```json
    {
      "supplier_id": 123,
      "items": [{"sku": "WIDGET-001", "quantity": 100}],
      "auto_receive": true
    }
    ```
    """
    # Import generated API methods
    from katana_public_api_client.api.purchase_order import (
        create_purchase_order_asyncio_detailed,
        receive_purchase_order_asyncio_detailed
    )

    services = get_services(context)

    # Step 1: Create PO using generated API
    po_response = await create_purchase_order_asyncio_detailed(
        client=services.client,
        json_body={
            "supplier_id": request.supplier_id,
            "items": request.items,
            "notes": request.notes
        }
    )
    po = po_response.parsed

    receipt = None
    if request.auto_receive:
        # Step 2: Receive items using generated API
        receipt_response = await receive_purchase_order_asyncio_detailed(
            client=services.client,
            id=po.id,
            json_body={
                "items": [
                    {"sku": item.sku, "quantity": item.quantity}
                    for item in request.items
                ]
            }
        )
        receipt = receipt_response.parsed

    # Step 3: Generate next actions
    next_actions = []
    if receipt:
        next_actions.append(f"Items received on PO #{po.number}")
        next_actions.append("Check inventory levels with check_inventory")
    else:
        next_actions.append(f"Receive items with receive_purchase_order(po_id={po.id})")

    return CreateAndReceivePOResponse(
        purchase_order=PurchaseOrderResponse.from_katana(po),
        receipt=ReceiveResponse.from_katana(receipt) if receipt else None,
        next_actions=next_actions
    )
````

**Benefits**:

- Foundation tools are simple and focused
- Workflow tools provide high-level intent
- Clear separation of concerns
- Workflows can reuse foundation logic
- Easy to test independently

______________________________________________________________________

## Migration Steps

### Phase 1: Structure Setup ✓

1. **Create directory structure**

   - `tools/foundation/` and `tools/workflows/`
   - `resources/` and `prompts/`
   - `services/`

1. **Update `server.py` with lifespan pattern**

   - Add `ServerContext` dataclass
   - Implement `lifespan()` async context manager
   - Update FastMCP initialization

1. **Create `dependencies.py`**

   - Add `Services` dataclass
   - Add `get_services()` helper

### Phase 2: Foundation Tools

Migrate existing tools to foundation layer:

1. **`tools/foundation/variants.py`**

   - `search_variants`
   - `get_variant_details`
   - `check_inventory`

1. **`tools/foundation/products.py`**

   - `create_product`
   - `update_product`
   - `delete_product`

1. **`tools/foundation/materials.py`**

   - `create_material`
   - `update_material`

1. **`tools/foundation/purchase_orders.py`**

   - `create_purchase_order`
   - `get_purchase_order`
   - `receive_purchase_order`
   - `verify_order_document`

1. **`tools/foundation/manufacturing_orders.py`**

   - `create_manufacturing_order`
   - `get_manufacturing_order`
   - `complete_manufacturing_order`

1. **`tools/foundation/sales_orders.py`**

   - `get_sales_order`
   - `fulfill_order`

### Phase 3: Workflow Tools

Create high-level workflows:

1. **`tools/workflows/po_lifecycle.py`**

   - `create_and_receive_po` (combines create + receive)

1. **`tools/workflows/manufacturing.py`**

   - `create_and_complete_mo` (combines create + complete)

1. **`tools/workflows/document_verification.py`**

   - `verify_and_create_po` (verify doc + create PO)

### Phase 4: Resources

Implement MCP resources:

1. **`resources/inventory.py`**

   - `katana://inventory/items` - Paginated catalog
   - `katana://inventory/stock-movements` - Recent movements
   - `katana://inventory/stock-adjustments` - Manual adjustments

1. **`resources/orders.py`**

   - `katana://orders/sales` - Open sales orders
   - `katana://orders/purchase` - Open purchase orders
   - `katana://orders/manufacturing` - Active work orders

### Phase 5: Prompts

Implement MCP prompts:

1. **`prompts/po_workflow.py`**

   - `create_and_receive_po` prompt template

1. **`prompts/verify_document.py`**

   - `verify_and_create_po` prompt template

1. **`prompts/fulfill_order.py`**

   - `fulfill_order` prompt template

### Phase 6: Testing & Documentation

1. **Update tests**

   - Mock context fixtures in `conftest.py`
   - Test foundation tools
   - Test workflow tools
   - Test resources
   - Test prompts

1. **Update documentation**

   - Tool reference docs
   - Workflow guides
   - Claude Desktop setup
   - Docker deployment

______________________________________________________________________

## Key Differences from Original Plan

### What We're Adopting from StockTrim

1. ✅ **Foundation/Workflow Split** - Clear two-tier organization
1. ✅ **Registration Pattern** - Deferred registration avoids circular imports
1. ✅ **Lifespan Management** - Proper client lifecycle
1. ✅ **Dependencies Helper** - Clean DI pattern
1. ✅ **Separate `_impl` Functions** - Better testability
1. ✅ **Services Layer** - Shared logic base class

### What We're Keeping from Original Plan

1. ✅ **Elicitation Pattern** - `confirm=false` preview mode
1. ✅ **Resources** - 6 resources (StockTrim doesn't have these yet)
1. ✅ **Prompts** - 3 workflow prompts (StockTrim doesn't have these yet)
1. ✅ **Next Actions** - Response guidance
1. ✅ **Three-Level Documentation** - Description + Fields + Extended docs
1. ✅ **Domain Models** - KatanaVariant, KatanaProduct (from Pydantic work)

______________________________________________________________________

## Configuration Updates

### Root `pyproject.toml`

```toml
[tool.ruff]
src = [
  "katana_public_api_client",
  "tests",
  "scripts",
  "katana_mcp_server/src",      # Add MCP server
  "katana_mcp_server/tests"
]
```

### MCP Server `pyproject.toml`

```toml
[project]
name = "katana-mcp-server"
version = "0.1.0"
requires-python = ">=3.11,<3.14"
dependencies = [
  "katana-openapi-client",     # Workspace dependency
  "fastmcp>=0.3.0",
  "python-dotenv>=1.0.0",
]

[tool.uv.sources]
katana-openapi-client = { workspace = true }

[project.scripts]
katana-mcp-server = "katana_mcp_server.server:main"

[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
tag_format = "mcp-v{version}"
commit_message = "chore(release): mcp v{version}"

[tool.semantic_release.commit_parser_options]
# Only process commits with (mcp) scope
allowed_tags = ["feat", "fix", "perf"]
minor_tags = ["feat"]
patch_tags = ["fix", "perf"]
default_bump_level = 0
```

______________________________________________________________________

## Success Criteria

### v0.1.0 Complete When:

- [ ] All 10 foundation tools implemented and tested
- [ ] All 3 workflow tools implemented and tested
- [ ] All 6 resources implemented and tested
- [ ] All 3 prompts implemented and tested
- [ ] Lifespan management working
- [ ] Console script entry point working
- [ ] Tests passing with mock fixtures
- [ ] Documentation complete
- [ ] Claude Desktop integration verified
- [ ] Example conversations documented

______________________________________________________________________

## References

- **StockTrim MCP Server**: https://github.com/dougborg/stocktrim-openapi-client/
- **Original Katana Plan**:
  [MCP_V0.1.0_IMPLEMENTATION_PLAN.md](MCP_V0.1.0_IMPLEMENTATION_PLAN.md)
- **Architecture Design**: [MCP_ARCHITECTURE_DESIGN.md](MCP_ARCHITECTURE_DESIGN.md)
- **ADR-010**: [../adr/0010-katana-mcp-server.md](../adr/0010-katana-mcp-server.md)
- **FastMCP Docs**: https://github.com/jlowin/fastmcp
