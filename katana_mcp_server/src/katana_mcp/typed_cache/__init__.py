"""#342 SQLModel-backed cache for transactional list tools.

Coexists with the legacy generic ``katana_mcp.cache.CatalogCache`` during
the per-entity rollout. Legacy cache holds the 10 reference entity types
(variants, products, suppliers, etc.); this typed cache holds
transactional types (sales orders first, more to follow). Legacy cache
retires once all reference types have migrated.

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
from .sync import ensure_sales_orders_synced, ensure_stock_adjustments_synced
from .sync_state import SyncState

__all__ = [
    "SyncState",
    "TypedCacheEngine",
    "ensure_sales_orders_synced",
    "ensure_stock_adjustments_synced",
]
