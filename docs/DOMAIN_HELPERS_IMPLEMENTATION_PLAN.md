# Domain Helpers Implementation Plan

This document outlines the implementation plan for domain helper classes as defined in
[ADR-007](adr/0007-domain-helper-classes.md).

## Purpose

Domain helpers provide a reusable business logic layer that sits between the raw OpenAPI
client and higher-level applications (like the MCP Server). They serve two critical
purposes:

1. **For Python Users**: Provide ergonomic, domain-specific methods that reduce
   boilerplate
1. **For MCP Server**: Serve as the foundation layer for MCP tools, enabling thin
   wrapper implementations

## Architecture

```
┌─────────────────────────────────────┐
│  Generated OpenAPI Client (raw API) │  ← Source of truth
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Domain Helpers (business logic)   │  ← This implementation
│   - InventoryHelper                 │
│   - SalesOrderHelper                │
│   - PurchaseOrderHelper             │
│   - ManufacturingOrderHelper        │
└──────────────┬──────────────────────┘
               │
               ├──────────────────┬─────────────────┐
               ↓                  ↓                 ↓
         ┌──────────┐      ┌──────────┐     ┌──────────┐
         │  Direct  │      │   MCP    │     │  Other   │
         │  Users   │      │  Tools   │     │  Apps    │
         └──────────┘      └──────────┘     └──────────┘
```

## Scope - Minimal MCP-Focused Implementation

Based on the MCP tool requirements (see
[MCP Implementation Plan](mcp-server/IMPLEMENTATION_PLAN.md)), we need domain helpers
for 12 MCP tools across 4 domains. This implementation focuses on **exactly what the MCP
tools need** - no more, no less.

### Phase 1: Inventory Helpers (Required by 3 MCP Tools + CRUD)

**MCP Tools**: check_inventory (#35), list_low_stock_items (#36), search_products (#37)

**Additional Requirement**: Full CRUD support for Products, Materials, Variants, and
Services

**InventoryHelper Methods**:

```python
class InventoryHelper:
    # === Stock & Search (MCP Tool Support) ===

    async def check_stock(self, sku: str) -> ProductStock:
        """Check stock levels for a specific SKU.

        Used by: MCP tool check_inventory
        """

    async def list_low_stock(self, threshold: int | None = None) -> list[ProductStock]:
        """Find products below their reorder point.

        Used by: MCP tool list_low_stock_items
        """

    async def search_products(self, query: str, limit: int = 50) -> list[Product]:
        """Search products by name or SKU.

        Used by: MCP tool search_products
        """

    # === Product CRUD ===

    async def list_products(self, **filters) -> list[Product]:
        """List all products with optional filters."""

    async def get_product(self, product_id: int) -> Product:
        """Get a specific product by ID."""

    async def create_product(self, product_data: dict) -> Product:
        """Create a new product."""

    async def update_product(self, product_id: int, product_data: dict) -> Product:
        """Update an existing product."""

    async def delete_product(self, product_id: int) -> None:
        """Delete a product."""

    # === Material CRUD ===

    async def list_materials(self, **filters) -> list[Material]:
        """List all materials with optional filters."""

    async def get_material(self, material_id: int) -> Material:
        """Get a specific material by ID."""

    async def create_material(self, material_data: dict) -> Material:
        """Create a new material."""

    async def update_material(self, material_id: int, material_data: dict) -> Material:
        """Update an existing material."""

    async def delete_material(self, material_id: int) -> None:
        """Delete a material."""

    # === Variant CRUD ===

    async def list_variants(self, **filters) -> list[Variant]:
        """List all variants with optional filters."""

    async def get_variant(self, variant_id: int) -> Variant:
        """Get a specific variant by ID."""

    async def create_variant(self, variant_data: dict) -> Variant:
        """Create a new variant."""

    async def update_variant(self, variant_id: int, variant_data: dict) -> Variant:
        """Update an existing variant."""

    async def delete_variant(self, variant_id: int) -> None:
        """Delete a variant."""

    # === Service CRUD ===

    async def list_services(self, **filters) -> list[Service]:
        """List all services with optional filters."""

    async def get_service(self, service_id: int) -> Service:
        """Get a specific service by ID."""

    async def create_service(self, service_data: dict) -> Service:
        """Create a new service."""

    async def update_service(self, service_id: int, service_data: dict) -> Service:
        """Update an existing service."""

    async def delete_service(self, service_id: int) -> None:
        """Delete a service."""
```

**Estimate**: 20-28 hours

- 3 MCP tool methods × 2-3 hours each (6-9h)
- 4 entity types × 5 CRUD operations × 1 hour each (20h)
- Helper class infrastructure (2-3h)
- Integration with KatanaClient (2-3h)
- Comprehensive testing (8-10h)

### Phase 2: Sales Order Helpers (Required by 3 MCP Tools)

**MCP Tools**: create_sales_order (#38), get_sales_order_status (#39),
list_recent_sales_orders (#40)

**SalesOrderHelper Methods**:

```python
class SalesOrderHelper:
    async def create(self, order_data: dict) -> SalesOrder:
        """Create a new sales order.

        Used by: MCP tool create_sales_order
        """

    async def get_status(self, order_id: int) -> SalesOrderStatus:
        """Get details and status of a sales order.

        Used by: MCP tool get_sales_order_status
        """

    async def list_recent(self, limit: int = 50) -> list[SalesOrder]:
        """List recent sales orders.

        Used by: MCP tool list_recent_sales_orders
        """
```

**Estimate**: 10-14 hours

- 3 methods × 3-4 hours each (create is more complex)
- Integration tests with actual API

### Phase 3: Purchase Order Helpers (Required by 3 MCP Tools)

**MCP Tools**: create_purchase_order (#41), get_purchase_order_status (#42),
receive_purchase_order (#43)

**PurchaseOrderHelper Methods**:

```python
class PurchaseOrderHelper:
    async def create(self, order_data: dict) -> PurchaseOrder:
        """Create a new purchase order.

        Used by: MCP tool create_purchase_order
        """

    async def get_status(self, order_id: int) -> PurchaseOrderStatus:
        """Get details and status of a purchase order.

        Used by: MCP tool get_purchase_order_status
        """

    async def receive(self, order_id: int, items: list[dict] | None = None) -> PurchaseOrder:
        """Mark purchase order as received.

        Used by: MCP tool receive_purchase_order
        """
```

**Estimate**: 10-14 hours

- 3 methods × 3-4 hours each
- Batch transaction handling for receive()

### Phase 4: Manufacturing Order Helpers (Required by 3 MCP Tools)

**MCP Tools**: create_manufacturing_order (#44), get_manufacturing_order_status (#45),
list_active_manufacturing_orders (#46)

**ManufacturingOrderHelper Methods**:

```python
class ManufacturingOrderHelper:
    async def create(self, order_data: dict) -> ManufacturingOrder:
        """Create a new manufacturing order.

        Used by: MCP tool create_manufacturing_order
        """

    async def get_status(self, order_id: int) -> ManufacturingOrderStatus:
        """Get details and status of a manufacturing order.

        Used by: MCP tool get_manufacturing_order_status
        """

    async def list_active(self) -> list[ManufacturingOrder]:
        """List in-progress manufacturing orders.

        Used by: MCP tool list_active_manufacturing_orders
        """
```

**Estimate**: 10-14 hours

- 3 methods × 3-4 hours each
- Production details handling

## Total Estimate

**Time**: 50-70 hours (approximately 1.5-2 weeks for 1 developer, or 1 week for 2
developers working in parallel)

**Breakdown**:

- Phase 1 (Inventory with CRUD): 20-28h
- Phase 2 (Sales Orders): 10-14h
- Phase 3 (Purchase Orders): 10-14h
- Phase 4 (Manufacturing): 10-14h

**CRUD Methods Added**:

- Products: 5 methods (list, get, create, update, delete)
- Materials: 5 methods (list, get, create, update, delete)
- Variants: 5 methods (list, get, create, update, delete)
- Services: 5 methods (list, get, create, update, delete)
- **Total**: 20 additional CRUD methods + 3 MCP-specific methods + 9 order helper
  methods = **32 helper methods**

## Implementation Strategy

### File Structure

```
katana_public_api_client/
├── helpers/
│   ├── __init__.py              # Export all helpers
│   ├── base.py                  # BaseHelper with client reference
│   ├── inventory.py             # InventoryHelper
│   ├── sales_orders.py          # SalesOrderHelper
│   ├── purchase_orders.py       # PurchaseOrderHelper
│   └── manufacturing_orders.py  # ManufacturingOrderHelper
├── katana_client.py             # Add helper properties
└── ...

tests/helpers/
├── test_inventory.py
├── test_sales_orders.py
├── test_purchase_orders.py
└── test_manufacturing_orders.py
```

### Integration with KatanaClient

```python
# katana_client.py
from katana_public_api_client.helpers import (
    InventoryHelper,
    SalesOrderHelper,
    PurchaseOrderHelper,
    ManufacturingOrderHelper,
)

class KatanaClient(AuthenticatedClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._inventory = None
        self._sales_orders = None
        self._purchase_orders = None
        self._manufacturing_orders = None

    @property
    def inventory(self) -> InventoryHelper:
        if self._inventory is None:
            self._inventory = InventoryHelper(self)
        return self._inventory

    @property
    def sales_orders(self) -> SalesOrderHelper:
        if self._sales_orders is None:
            self._sales_orders = SalesOrderHelper(self)
        return self._sales_orders

    # ... similar for purchase_orders and manufacturing_orders
```

### Testing Strategy

1. **Unit Tests**: Mock API responses, test business logic
1. **Integration Tests**: Use actual API with test data (requires KATANA_API_KEY)
1. **Coverage Target**: 80%+ for helper code

### Documentation

1. Update [KATANA_CLIENT_GUIDE.md](KATANA_CLIENT_GUIDE.md) with helper examples
1. Add docstrings with clear "Used by" references to MCP tools
1. Update [COOKBOOK.md](COOKBOOK.md) with helper-based recipes

## Dependency Impact on MCP Implementation

### Current Dependency Chain (Without Helpers)

```
#32 (workspace) → #33 (package) → #34 (basic server) → #35-46 (all 12 tools)
```

**Problem**: All 12 tool issues would implement redundant business logic

### New Dependency Chain (With Helpers)

```
#32 (workspace) → #33 (package) → #NEW (domain helpers) → #34 (basic server) → #35-46 (tools as thin wrappers)
```

**Benefit**: Tool issues become trivial wrappers, estimated time for each tool reduces
by 30-50%

### MCP Tool Simplification Example

**Before (No Helpers)** - check_inventory tool:

```python
@mcp.tool()
async def check_inventory(sku: str, ctx: Context) -> InventoryStatus:
    """Check stock levels for a specific SKU."""
    async with KatanaClient() as client:
        # 20+ lines of API calls, pagination, error handling, filtering...
        response = await get_all_products.asyncio_detailed(
            client=client,
            sku=sku,
            include_stock_information=True,
            limit=100
        )
        products = unwrap_data(response)
        # ... more logic ...
        return InventoryStatus(...)
```

**After (With Helpers)** - check_inventory tool:

```python
@mcp.tool()
async def check_inventory(sku: str, ctx: Context) -> InventoryStatus:
    """Check stock levels for a specific SKU."""
    async with KatanaClient() as client:
        stock = await client.inventory.check_stock(sku)
        return InventoryStatus(
            sku=stock.sku,
            available=stock.available,
            allocated=stock.allocated,
            in_stock=stock.in_stock
        )
```

**Time Savings**:

- Tool implementation: 4-6h → 2-3h (50% reduction)
- Tool testing: Mostly just MCP interface tests, business logic already tested
- Total across 12 tools: ~24-36 hours saved

## Success Metrics

- [ ] 4 helper classes implemented (Inventory, Sales Orders, Purchase Orders,
  Manufacturing)
- [ ] 32 domain methods total:
  - 3 MCP-specific inventory methods (check_stock, list_low_stock, search_products)
  - 20 CRUD methods for core entities (Products, Materials, Variants, Services)
  - 9 order helper methods (Sales/Purchase/Manufacturing Orders)
- [ ] 80%+ test coverage for helper code
- [ ] All helper methods documented with "Used by" MCP tool references where applicable
- [ ] Helper properties added to KatanaClient (inventory, sales_orders, purchase_orders,
  manufacturing_orders)
- [ ] Integration tests passing with actual Katana API
- [ ] KATANA_CLIENT_GUIDE.md updated with helper examples
- [ ] CRUD operations enable full MCP tool coverage for inventory management

## Next Steps

1. Create GitHub issue for domain helpers implementation
1. Update MCP implementation plan to add domain helpers dependency
1. Implement Phase 1 (Inventory) first to validate approach
1. Implement remaining phases in parallel if multiple developers available
1. Update MCP tool issues to reference helper methods they'll use

## References

- [ADR-007: Generate Domain Helper Classes](adr/0007-domain-helper-classes.md)
- [ADR-010: Katana MCP Server](adr/0010-katana-mcp-server.md)
- [MCP Implementation Plan](mcp-server/IMPLEMENTATION_PLAN.md)
- [MCP Issues JSON](mcp-server/issues.json)
