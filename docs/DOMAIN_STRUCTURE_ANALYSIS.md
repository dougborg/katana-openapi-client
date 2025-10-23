# Domain Structure Analysis

## Problem Statement

Initial implementation conflated "inventory" (stock levels/movements) with
"products/materials/variants" (catalog entities). Need to properly separate concerns.

## Katana API Structure Analysis

### Actual Inventory Operations

**Module**: `inventory/`

- `get_all_inventory_point` - Current inventory levels
- `get_all_negative_stock` - Items with negative stock
- `create_inventory_reorder_point` - Set reorder points
- `create_inventory_safety_stock_level` - Set safety stock

**Module**: `inventory_movements/`

- `get_all_inventory_movements` - Historical stock movements

**Module**: `stock_adjustment/`

- CRUD operations for stock adjustments (manual corrections)

**Module**: `stock_transfer/`

- Transfer stock between locations

**Module**: `stocktake/` & `stocktake_row/`

- Physical inventory counts

### Catalog/Product Management

**Module**: `product/`

- CRUD operations for products

**Module**: `material/`

- CRUD operations for materials

**Module**: `variant/`

- CRUD operations for product variants

**Module**: `services/`

- CRUD operations for services

## Proposed Domain Structure

### Option A: Separate Domains (Recommended)

```python
client.products      # Product catalog CRUD
client.materials     # Material catalog CRUD
client.variants      # Variant catalog CRUD
client.services      # Service catalog CRUD
client.inventory     # Stock levels, movements, adjustments
client.sales_orders  # Sales order operations
client.purchase_orders  # Purchase order operations
client.manufacturing_orders  # Manufacturing order operations
```

**Pros**:

- Clear separation of concerns
- Matches Katana's API structure
- Intuitive: "products" = catalog, "inventory" = stock
- Each domain has focused responsibility

**Cons**:

- More domain classes to maintain
- Product/material/variant/service might be similar (but that's OK - DRY via Base class)

### Option B: Combined Catalog Domain

```python
client.catalog       # Products, materials, variants, services CRUD
client.inventory     # Stock levels, movements, adjustments
client.sales_orders
client.purchase_orders
client.manufacturing_orders
```

**Pros**:

- Single entry point for all catalog entities
- Fewer top-level domain classes

**Cons**:

- `client.catalog.create_product()` is less intuitive than `client.products.create()`
- Mixes different entity types in one class

### Option C: Nested Structure

```python
client.catalog.products     # Product CRUD
client.catalog.materials    # Material CRUD
client.catalog.variants     # Variant CRUD
client.catalog.services     # Service CRUD
client.inventory            # Stock operations
```

**Pros**:

- Logical grouping
- Clear hierarchy

**Cons**:

- Extra nesting layer (`client.catalog.products` vs `client.products`)
- More complex property management

## Recommendation: Option A

**Rationale**:

1. **Clearest API**: `client.products.create()` is more intuitive than
   `client.catalog.create_product()`
1. **Matches Katana**: Katana's API has separate modules for each
1. **Focused domains**: Each class has single responsibility
1. **Future-proof**: Easy to add more domains (customers, suppliers, etc.)

## Revised Domain Classes

### 1. Products

```python
class Products(Base):
    async def list(**filters) -> list[Product]
    async def get(product_id) -> Product
    async def create(data) -> Product
    async def update(product_id, data) -> Product
    async def delete(product_id) -> None
    async def search(query, limit=50) -> list[Product]  # Helper for MCP tool
```

### 2. Materials

```python
class Materials(Base):
    async def list(**filters) -> list[Material]
    async def get(material_id) -> Material
    async def create(data) -> Material
    async def update(material_id, data) -> Material
    async def delete(material_id) -> None
```

### 3. Variants

```python
class Variants(Base):
    async def list(**filters) -> list[Variant]
    async def get(variant_id) -> Variant
    async def create(data) -> Variant
    async def update(variant_id, data) -> Variant
    async def delete(variant_id) -> None
```

### 4. Services

```python
class Services(Base):
    async def list(**filters) -> list[Service]
    async def get(service_id) -> Service
    async def create(data) -> Service
    async def update(service_id, data) -> Service
    async def delete(service_id) -> None
```

### 5. Inventory (Stock Operations)

```python
class Inventory(Base):
    # MCP Tool Support
    async def check_stock(sku) -> dict  # Checks product stock by SKU
    async def list_low_stock(threshold) -> list[dict]  # Products below threshold

    # Inventory levels
    async def get_inventory_points(**filters) -> list
    async def get_negative_stock() -> list
    async def set_reorder_point(product_id, quantity) -> None
    async def set_safety_stock(product_id, quantity) -> None

    # Stock movements
    async def get_movements(**filters) -> list

    # Stock adjustments
    async def list_adjustments(**filters) -> list
    async def create_adjustment(data) -> StockAdjustment
    async def update_adjustment(adjustment_id, data) -> StockAdjustment
    async def delete_adjustment(adjustment_id) -> None

    # Stock transfers
    async def create_transfer(from_location, to_location, items) -> StockTransfer

    # Stocktakes
    async def list_stocktakes(**filters) -> list
    async def create_stocktake(data) -> Stocktake
```

## Impact on MCP Tools

### MCP Tool: check_inventory

**Original plan**: `client.inventory.check_stock()` **New structure**:
`client.inventory.check_stock()` ✅ (same!)

Note: This method will internally use `client.products.list()` to look up by SKU, then
return stock info.

### MCP Tool: search_products

**Original plan**: `client.inventory.search_products()` **New structure**:
`client.products.search()` ✅ (better!)

### MCP Tool: list_low_stock_items

**Original plan**: `client.inventory.list_low_stock()` **New structure**:
`client.inventory.list_low_stock()` ✅ (same!)

## Migration Plan

### Current State (PR #62)

- Single `Inventory` class with 23 methods
- Mixes catalog CRUD with stock operations

### Target State

- 5 separate domain classes: Products, Materials, Variants, Services, Inventory
- Each focused on specific responsibility
- ~35-40 total methods across all classes

### Steps

1. Keep PR #62 open but mark as WIP/draft
1. Create new branch with correct structure
1. Split current `inventory.py` into:
   - `products.py` (6 methods: 5 CRUD + search)
   - `materials.py` (5 CRUD methods)
   - `variants.py` (5 CRUD methods)
   - `services.py` (5 CRUD methods)
   - `inventory.py` (15+ stock operation methods)
1. Update `KatanaClient` with all 5 properties
1. Update documentation and tests

## Estimated Effort

**Original estimate**: 20-28h for single Inventory class **New estimate**: 25-35h for 5
properly separated classes

- Products: 5-7h (includes search helper + MCP integration)
- Materials: 3-4h
- Variants: 3-4h
- Services: 3-4h
- Inventory: 8-12h (stock operations + MCP helpers)
- Testing & docs: 3-4h

**Trade-off**: Slightly more time, but much cleaner architecture that matches Katana's
domain model.
