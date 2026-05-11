"""SQLModel-backed typed cache for Katana entities (#342, ADR-0018, #472).

``TypedCacheEngine`` holds all cached entity types (catalog +
transactional) in per-entity SQLModel tables with proper FK relationships
and JSON columns. The legacy ``katana_mcp.cache.CatalogCache`` was
retired in #472 Phase D once ``services.typed_cache.catalog`` (a
:class:`CatalogQueries` adapter) replaced its read API and the catalog
``EntitySpec`` pipeline replaced its sync helpers — see ADR-0018 for
the original architectural framing.

End-state coverage:

- Catalog: variants, products, materials, services, customers,
  suppliers, locations, tax rates, operators, factories, additional
  costs (11 types). Search uses per-entity FTS5 virtual tables; the
  ``CatalogQueries`` adapter wraps ``smart_search`` / ``get_by_id`` /
  ``get_by_sku`` / ``get_many_by_ids`` / ``get_all`` /
  ``search_fuzzy`` with default ``include_archived=False`` /
  ``include_deleted=False`` filters.
- Transactional: sales orders, manufacturing orders (+ recipe rows),
  purchase orders (+ rows), stock adjustments, stock transfers (10
  ``Cached*`` siblings counting child rows). Search via SQL WHERE
  clauses; no FTS sidecar — these tables don't carry free-text fields.

Public API::

    from katana_mcp.typed_cache import (
        TypedCacheEngine,
        ensure_sales_orders_synced,
        ensure_variants_synced,
    )

    engine = TypedCacheEngine()
    await engine.open()
    try:
        await ensure_variants_synced(client, engine)
        # Typed lookups via the CatalogQueries adapter on engine.catalog.
        variant = await engine.catalog.get_by_sku("FOX-FORK-160")
        results = await engine.catalog.smart_search(
            CachedVariant, "kitchen knife"
        )
    finally:
        await engine.close()
"""

from __future__ import annotations

from .engine import TypedCacheEngine
from .queries import CatalogQueries
from .sync import (
    ENTITY_SPECS,
    MANUFACTURING_ORDER_RECIPE_ROW_SPEC,
    MANUFACTURING_ORDER_SPEC,
    EntitySpec,
    ensure_additional_costs_synced,
    ensure_customers_synced,
    ensure_factory_synced,
    ensure_locations_synced,
    ensure_manufacturing_order_recipe_rows_synced,
    ensure_manufacturing_orders_synced,
    ensure_materials_synced,
    ensure_operators_synced,
    ensure_products_synced,
    ensure_purchase_orders_synced,
    ensure_sales_orders_synced,
    ensure_services_synced,
    ensure_stock_adjustments_synced,
    ensure_stock_transfers_synced,
    ensure_suppliers_synced,
    ensure_tax_rates_synced,
    ensure_variants_synced,
    force_resync,
    merge_filtered_fetch,
)
from .sync_state import SyncState

__all__ = [
    "ENTITY_SPECS",
    "MANUFACTURING_ORDER_RECIPE_ROW_SPEC",
    "MANUFACTURING_ORDER_SPEC",
    "CatalogQueries",
    "EntitySpec",
    "SyncState",
    "TypedCacheEngine",
    "ensure_additional_costs_synced",
    "ensure_customers_synced",
    "ensure_factory_synced",
    "ensure_locations_synced",
    "ensure_manufacturing_order_recipe_rows_synced",
    "ensure_manufacturing_orders_synced",
    "ensure_materials_synced",
    "ensure_operators_synced",
    "ensure_products_synced",
    "ensure_purchase_orders_synced",
    "ensure_sales_orders_synced",
    "ensure_services_synced",
    "ensure_stock_adjustments_synced",
    "ensure_stock_transfers_synced",
    "ensure_suppliers_synced",
    "ensure_tax_rates_synced",
    "ensure_variants_synced",
    "force_resync",
    "merge_filtered_fetch",
]
