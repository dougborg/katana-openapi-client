"""SQLModel-backed cache for transactional list tools (#342, ADR-0018).

Complements ``katana_mcp.cache.CatalogCache`` — the two caches serve
different concerns and both are permanent:

- **CatalogCache** holds the 10 reference entity types (variants, products,
  materials, services, suppliers, customers, locations, tax rates,
  operators, factories) in a generic SQLite + FTS5 store. Powers
  ``search_items`` / ``get_variant_details`` and other lookup tools.
- **TypedCacheEngine** (this package) holds transactional types
  (sales_orders, manufacturing_orders, purchase_orders, stock_adjustments,
  stock_transfers, manufacturing_order_recipe_rows) in per-entity SQLModel
  tables with proper FK relationships and JSON columns. Powers the
  cache-backed ``list_*`` tools.

The transactional types' richer filter needs (status, customer/supplier
IDs, date ranges, variant-id-via-rows) and 30+-field schemas don't fit
``CatalogCache``'s three-text-column ``entity_index`` projection — see
ADR-0018 for the full rationale. The two caches will continue to coexist.

Public API::

    from katana_mcp.typed_cache import (
        TypedCacheEngine,
        ensure_sales_orders_synced,
    )

    engine = TypedCacheEngine()
    await engine.open()
    try:
        await ensure_sales_orders_synced(client, engine)
        async with engine.session() as session:
            orders = (await session.exec(select(SalesOrder))).all()
    finally:
        await engine.close()
"""

from __future__ import annotations

from .engine import TypedCacheEngine
from .sync import (
    ensure_manufacturing_order_recipe_rows_synced,
    ensure_manufacturing_orders_synced,
    ensure_purchase_orders_synced,
    ensure_sales_orders_synced,
    ensure_stock_adjustments_synced,
    ensure_stock_transfers_synced,
)
from .sync_state import SyncState

__all__ = [
    "SyncState",
    "TypedCacheEngine",
    "ensure_manufacturing_order_recipe_rows_synced",
    "ensure_manufacturing_orders_synced",
    "ensure_purchase_orders_synced",
    "ensure_sales_orders_synced",
    "ensure_stock_adjustments_synced",
    "ensure_stock_transfers_synced",
]
