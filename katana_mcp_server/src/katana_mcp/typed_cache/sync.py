"""Per-entity cache sync against the Katana API.

One generic ``_ensure_synced(client, cache, spec)`` drives every entity's
sync via an :class:`EntitySpec` configuration object. Each spec wires up:

- the entity-key string (used for the per-entity lock and ``SyncState`` row),
- the ``asyncio_detailed`` API endpoint to call,
- the cache row class (``Cached<Entity>``) and the API pydantic class
  (used as the ``from_attrs`` intermediary so nested-row conversion stays
  in one well-tested place),
- optional child-rows configuration (class, parent-side field name, FK
  field name) for entities with nested rows on the wire,
- an optional ``pydantic_resolver`` that picks the API pydantic subclass
  from the attrs object (used by purchase orders, where Katana returns a
  discriminated union ``RegularPurchaseOrder | OutsourcedPurchaseOrder``).

Public ``ensure_<entity>_synced(client, cache)`` functions are thin
wrappers over ``_ensure_synced`` so existing call sites and tests don't
need to change.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlmodel import delete

from katana_public_api_client.api.manufacturing_order import (
    get_all_manufacturing_orders,
)
from katana_public_api_client.api.manufacturing_order_recipe import (
    get_all_manufacturing_order_recipe_rows,
)
from katana_public_api_client.api.purchase_order import find_purchase_orders
from katana_public_api_client.api.purchase_order_row import (
    get_all_purchase_order_rows,
)
from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.api.sales_order_row import get_all_sales_order_rows
from katana_public_api_client.api.stock_adjustment import get_all_stock_adjustments
from katana_public_api_client.api.stock_transfer import get_all_stock_transfers
from katana_public_api_client.models_pydantic._generated import (
    CachedManufacturingOrder,
    CachedManufacturingOrderRecipeRow,
    CachedPurchaseOrder,
    CachedPurchaseOrderRow,
    CachedSalesOrder,
    CachedSalesOrderRow,
    CachedStockAdjustment,
    CachedStockAdjustmentRow,
    CachedStockTransfer,
    CachedStockTransferRow,
    ManufacturingOrder as PydanticManufacturingOrder,
    ManufacturingOrderRecipeRow as PydanticManufacturingOrderRecipeRow,
    PurchaseOrderBase as PydanticPurchaseOrderBase,
    PurchaseOrderRow as PydanticPurchaseOrderRow,
    SalesOrder as PydanticSalesOrder,
    SalesOrderRow as PydanticSalesOrderRow,
    StockAdjustment as PydanticStockAdjustment,
    StockTransfer as PydanticStockTransfer,
)
from katana_public_api_client.models_pydantic._registry import get_pydantic_class
from katana_public_api_client.utils import unwrap_data

from .sync_state import SyncState

if TYPE_CHECKING:
    from katana_public_api_client import KatanaClient

    from .engine import TypedCacheEngine


@dataclass(frozen=True)
class EntitySpec:
    """Per-entity sync configuration consumed by ``_ensure_synced``.

    Required: ``entity_key`` (the lock + SyncState key — repeated three
    times in the prior hand-rolled helpers, source of silent-desync bugs
    if a typo slipped through), ``api_fn`` (the ``asyncio_detailed``-
    bearing endpoint module), ``cache_cls`` (``Cached<Entity>``), and
    ``pydantic_cls`` (the API pydantic class — the ``from_attrs`` /
    ``model_dump`` intermediary).

    Optional: a ``child_cls`` + ``rows_field`` + ``fk_field`` triple when
    the entity has nested rows; without them the sync emits a parent-only
    row pair (the manufacturing-order list endpoint shape).
    ``pydantic_resolver`` overrides ``pydantic_cls`` per-row by dispatching
    on the attrs subclass — used by purchase orders, where the
    discriminated-union root would otherwise lose subclass-only fields.

    ``related_specs`` is for entities whose rows live at a *separate* API
    endpoint with their own watermark (manufacturing orders + recipe
    rows: rows aren't nested in the MO response, so the nested-rows
    triple above doesn't apply). Listing them here means
    ``_ensure_synced`` fans out to sync them in parallel, so consumers
    that join parent ↔ child in cache can call a single
    ``ensure_<parent>_synced`` and trust that both sides are fresh —
    no caller-side ``asyncio.gather`` to forget.
    """

    entity_key: str
    api_fn: Any
    cache_cls: type
    pydantic_cls: type
    child_cls: type | None = None
    rows_field: str | None = None
    fk_field: str | None = None
    pydantic_resolver: Callable[[Any], type] | None = None
    related_specs: tuple[EntitySpec, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        # Children are configured by a ``(child_cls, rows_field, fk_field)``
        # triple — a partial set would silently drop children at runtime
        # because ``_convert`` only iterates when all three are present.
        # Catch the typo at construction time instead.
        triple = (self.child_cls, self.rows_field, self.fk_field)
        n_set = sum(value is not None for value in triple)
        if n_set not in (0, 3):
            msg = (
                "EntitySpec child_cls/rows_field/fk_field must all be "
                "set together or all left as None"
            )
            raise ValueError(msg)


def _resolve_purchase_order_class(attrs_po: Any) -> type:
    """Pick the right pydantic subclass for a purchase-order attrs object.

    ``RegularPurchaseOrder`` and ``OutsourcedPurchaseOrder`` share
    ``PurchaseOrderBase`` fields but differ in ``entity_type`` and the
    outsourced-only ``tracking_location_id`` / ``ingredient_*`` fields.
    Calling ``PydanticPurchaseOrderBase.from_attrs`` directly would lose
    those subclass-only fields; the registry keeps the subtype.
    """

    api_class = get_pydantic_class(type(attrs_po))
    if api_class is None:
        msg = (
            f"No pydantic class registered for attrs purchase order "
            f"type {type(attrs_po).__name__}"
        )
        raise RuntimeError(msg)
    return api_class


def _convert(spec: EntitySpec, attrs_obj: Any) -> tuple[Any, list[Any]]:
    """Convert one attrs API object to a ``(parent, children)`` cache pair.

    Two-step:
    1. The API pydantic class (resolved via ``pydantic_resolver`` or
       ``spec.pydantic_cls``) handles UNSET → None, enum extraction,
       datetime coercion, and registry-driven nested-row conversion via
       ``from_attrs``.
    2. ``model_dump`` exports a plain dict; the cache class's
       ``model_validate`` reconstructs the parent (excluding the rows
       relationship — SQLModel ``Relationship`` descriptors don't accept
       input via ``__init__`` / ``model_validate``). Children, if
       configured, are re-built as the cache row class with the FK set
       explicitly from the parent's ``id`` so SQLAlchemy can wire the
       link on insert.

    Re-asserting the FK from the parent guards against the wire shape
    silently changing on entities (sales orders, purchase orders) where
    Katana already returns the FK on rows; for entities where Katana
    nests rows under the parent without a back-pointer (stock adjustments,
    stock transfers), the FK is synthesized here.
    """
    api_cls = (
        spec.pydantic_resolver(attrs_obj)
        if spec.pydantic_resolver is not None
        else spec.pydantic_cls
    )
    api_obj = api_cls.from_attrs(attrs_obj)

    exclude = {spec.rows_field} if spec.rows_field else set()
    parent = spec.cache_cls.model_validate(api_obj.model_dump(exclude=exclude))

    children: list[Any] = []
    if (
        spec.child_cls is not None
        and spec.rows_field is not None
        and spec.fk_field is not None
    ):
        api_rows = getattr(api_obj, spec.rows_field) or []
        for api_row in api_rows:
            row_data = api_row.model_dump()
            row_data[spec.fk_field] = api_obj.id
            children.append(spec.child_cls.model_validate(row_data))

    return parent, children


async def _ensure_synced(
    client: KatanaClient, cache: TypedCacheEngine, spec: EntitySpec
) -> None:
    """Pull updated rows for one entity from Katana and upsert into the cache.

    Every call hits the API. Cold-start fetches the full history (cost
    scales with row count); subsequent calls pass
    ``updated_at_min=<last_synced>`` so the API returns only the delta
    since the previous sync — typically zero rows, ~100-200ms RTT for
    the empty response. The per-entity lock guarantees only one sync
    runs at a time even when multiple tool calls land concurrently
    (the second waits, then issues its own — also typically empty —
    delta fetch). We deliberately do not debounce: an explicit TTL
    layer hides MCP-driven mutations and out-of-band UI edits behind
    a stale window for no real saving, since the delta fetch is
    already cheap.

    Soft-deletes are folded in by passing ``include_deleted=True``: when
    a row is deleted in the Katana UI, the next incremental fetch returns
    it with ``deleted_at`` populated, and the upsert path naturally
    propagates that timestamp into the cache row. The cache classes all
    extend ``DeletableEntity`` (a ``deleted_at`` column ships natively),
    and every ``list_*`` query already filters ``deleted_at IS NULL``, so
    no ghost rows leak to callers and the historical record survives in
    the cache for any future audit/reporting need. We mirror Katana's own
    soft-delete model rather than hard-deleting locally.

    ``spec.related_specs`` triggers parallel sync of sibling entities
    (e.g. manufacturing-order recipe rows when MOs are synced) so a
    consumer joining parent ↔ child in cache only needs to call one
    ``ensure_<parent>_synced``.
    """
    if spec.related_specs:
        await asyncio.gather(
            _sync_one(client, cache, spec),
            *(_ensure_synced(client, cache, related) for related in spec.related_specs),
        )
        return
    await _sync_one(client, cache, spec)


async def _sync_one(
    client: KatanaClient, cache: TypedCacheEngine, spec: EntitySpec
) -> None:
    """Sync exactly one entity (no related-spec fan-out).

    Split out from ``_ensure_synced`` so the related-spec gather doesn't
    re-enter the parent's lock recursively when a future child carries
    its own ``related_specs`` chain — each entity's sync runs under its
    own per-entity lock, no nesting.
    """
    async with cache.lock_for(spec.entity_key):
        await _sync_one_locked(client, cache, spec)


async def _sync_one_locked(
    client: KatanaClient, cache: TypedCacheEngine, spec: EntitySpec
) -> None:
    """Same sync work as ``_sync_one``, but assumes the caller already holds
    ``cache.lock_for(spec.entity_key)``.

    Used by :func:`force_resync` so the truncate and the cold-start re-pull
    happen under one continuous lock acquisition — concurrent ``list_*``
    tools block on the same lock until both phases finish and never observe
    an empty cache. ``_sync_one`` itself is the lock-acquiring wrapper for
    the normal incremental-sync path; calling it from ``force_resync`` while
    the lock is held would deadlock (asyncio.Lock isn't reentrant).
    """
    async with cache.session() as session:
        state = await session.get(SyncState, spec.entity_key)
        last_synced = state.last_synced if state is not None else None

    # ``last_synced`` is persisted as naive UTC (SQLite's default
    # DateTime column strips tzinfo). Re-attach UTC before sending to
    # the API so the generated client serializes an explicit offset.
    # ``include_deleted=True`` is always sent so soft-deletes after
    # the watermark surface in the response (Katana bumps
    # ``updated_at`` when ``deleted_at`` is set), letting the upsert
    # propagate the tombstone into the cache row.
    kwargs: dict[str, Any] = {"include_deleted": True}
    if last_synced is not None:
        kwargs["updated_at_min"] = last_synced.replace(tzinfo=UTC)
    response = await spec.api_fn.asyncio_detailed(client=client, **kwargs)
    attrs_objs = unwrap_data(response, default=[])

    cached_parents: list[Any] = []
    cached_children: list[Any] = []
    for attrs_obj in attrs_objs:
        parent, children = _convert(spec, attrs_obj)
        cached_parents.append(parent)
        cached_children.extend(children)

    async with cache.session() as session:
        # Parents first so child FK constraints resolve on insert.
        for parent in cached_parents:
            await session.merge(parent)
        for child in cached_children:
            await session.merge(child)
        # SQLite's DateTime column doesn't preserve tzinfo, so naive
        # UTC on the write side. ``row_count`` is the last-fetch size
        # (not a cumulative total, which would drift since a re-sync
        # that finds zero changed rows would otherwise reset the
        # count); consumers needing a true total run ``SELECT COUNT(*)``
        # on the entity table itself.
        await session.merge(
            SyncState(
                entity_type=spec.entity_key,
                last_synced=datetime.now(tz=UTC).replace(tzinfo=None),
                row_count=len(cached_parents),
            )
        )
        await session.commit()


# ---------------------------------------------------------------------------
# Per-entity specs
# ---------------------------------------------------------------------------


# Sales-order rows: nested under their parent in the ``find_sales_orders``
# response, but the response *hides* soft-deleted rows even with
# ``include_deleted=True`` (that flag controls top-level inclusion only).
# Without an independent row sync, a row deleted via ``delete_sales_order_row``
# on a still-live parent stays in the cache as a ghost. The dedicated
# ``/sales_order_rows`` endpoint exposes ``include_deleted`` + the same
# ``updated_at_min`` watermark mechanism, so we can pick up tombstones the
# parent response omits. Defined before ``_SALES_ORDER_SPEC`` so the parent's
# ``related_specs`` can reference it (frozen dataclasses can't forward-ref).
_SALES_ORDER_ROW_SPEC = EntitySpec(
    entity_key="sales_order_row",
    api_fn=get_all_sales_order_rows,
    cache_cls=CachedSalesOrderRow,
    pydantic_cls=PydanticSalesOrderRow,
)


_SALES_ORDER_SPEC = EntitySpec(
    entity_key="sales_order",
    api_fn=get_all_sales_orders,
    cache_cls=CachedSalesOrder,
    pydantic_cls=PydanticSalesOrder,
    child_cls=CachedSalesOrderRow,
    rows_field="sales_order_rows",
    fk_field="sales_order_id",
    related_specs=(_SALES_ORDER_ROW_SPEC,),
)


_STOCK_ADJUSTMENT_SPEC = EntitySpec(
    entity_key="stock_adjustment",
    api_fn=get_all_stock_adjustments,
    cache_cls=CachedStockAdjustment,
    pydantic_cls=PydanticStockAdjustment,
    child_cls=CachedStockAdjustmentRow,
    rows_field="stock_adjustment_rows",
    fk_field="stock_adjustment_id",
)


# Manufacturing-order recipe rows: fetched from the separate
# ``/manufacturing_order_recipe_rows`` endpoint, not nested under the MO
# parent — so they have their own ``updated_at_min`` watermark and sync
# lock. Direct conversion via the pydantic intermediary; ``batch_transactions``
# survives ``model_dump`` as a plain dict list and lands in the cache class's
# JSON column unchanged. Defined before the MO spec because the MO spec
# references it via ``related_specs`` (frozen dataclasses can't forward-
# reference each other).
_MANUFACTURING_ORDER_RECIPE_ROW_SPEC = EntitySpec(
    entity_key="manufacturing_order_recipe_row",
    api_fn=get_all_manufacturing_order_recipe_rows,
    cache_cls=CachedManufacturingOrderRecipeRow,
    pydantic_cls=PydanticManufacturingOrderRecipeRow,
)


# Manufacturing orders: the list endpoint returns summary objects with no
# nested rows. Recipe rows live at the sibling endpoint above and are
# pulled in via ``related_specs`` so any cache consumer that joins MO ↔
# recipe row (e.g. ``list_blocking_ingredients``) only needs to call
# ``ensure_manufacturing_orders_synced`` and trusts both watermarks have
# been advanced.
_MANUFACTURING_ORDER_SPEC = EntitySpec(
    entity_key="manufacturing_order",
    api_fn=get_all_manufacturing_orders,
    cache_cls=CachedManufacturingOrder,
    pydantic_cls=PydanticManufacturingOrder,
    related_specs=(_MANUFACTURING_ORDER_RECIPE_ROW_SPEC,),
)


# Purchase-order rows: like sales-order rows, ``find_purchase_orders``
# hides soft-deleted nested rows even with ``include_deleted=True`` set
# at the parent level. The ``/purchase_order_rows`` sibling endpoint
# (added to MCP via ``delete_purchase_order_row`` /
# ``update_purchase_order_row`` in #461) exposes ``include_deleted`` and
# its own watermark, so we sync rows independently to catch tombstones
# the parent response omits.
_PURCHASE_ORDER_ROW_SPEC = EntitySpec(
    entity_key="purchase_order_row",
    api_fn=get_all_purchase_order_rows,
    cache_cls=CachedPurchaseOrderRow,
    pydantic_cls=PydanticPurchaseOrderRow,
)


# Purchase orders: discriminated-union entity. The cache class shadows
# ``PurchaseOrderBase`` (renamed via ``CACHE_TABLE_RENAMES``) and carries
# an extra ``tracking_location_id`` column hoisted from the outsourced
# subclass via ``CACHE_EXTRA_FIELDS``. ``_resolve_purchase_order_class``
# picks the right subtype so ``model_dump`` captures the outsourced-only
# fields; ``CachedPurchaseOrder.model_validate`` ignores the
# unrecognized-by-the-cache extras automatically.
_PURCHASE_ORDER_SPEC = EntitySpec(
    entity_key="purchase_order",
    api_fn=find_purchase_orders,
    cache_cls=CachedPurchaseOrder,
    pydantic_cls=PydanticPurchaseOrderBase,
    child_cls=CachedPurchaseOrderRow,
    rows_field="purchase_order_rows",
    fk_field="purchase_order_id",
    pydantic_resolver=_resolve_purchase_order_class,
    related_specs=(_PURCHASE_ORDER_ROW_SPEC,),
)


_STOCK_TRANSFER_SPEC = EntitySpec(
    entity_key="stock_transfer",
    api_fn=get_all_stock_transfers,
    cache_cls=CachedStockTransfer,
    pydantic_cls=PydanticStockTransfer,
    child_cls=CachedStockTransferRow,
    rows_field="stock_transfer_rows",
    fk_field="stock_transfer_id",
)


# ---------------------------------------------------------------------------
# Public per-entity wrappers
# ---------------------------------------------------------------------------


async def ensure_sales_orders_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated sales orders from Katana and upsert into the typed cache."""
    await _ensure_synced(client, cache, _SALES_ORDER_SPEC)


async def ensure_stock_adjustments_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated stock adjustments from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _STOCK_ADJUSTMENT_SPEC)


async def ensure_manufacturing_orders_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated manufacturing orders from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _MANUFACTURING_ORDER_SPEC)


async def ensure_purchase_orders_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated purchase orders from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _PURCHASE_ORDER_SPEC)


async def ensure_stock_transfers_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated stock transfers from Katana and upsert into the cache."""
    await _ensure_synced(client, cache, _STOCK_TRANSFER_SPEC)


async def ensure_manufacturing_order_recipe_rows_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated MO recipe rows from Katana and upsert into the cache.

    Recipe rows are fetched from the separate
    ``/manufacturing_order_recipe_rows`` endpoint (not nested under the
    MO parent), so they have their own ``updated_at_min`` watermark and
    sync lock. ``ensure_manufacturing_orders_synced`` already fans out to
    this spec via ``related_specs``, so most callers don't need to call
    this helper directly — it's exposed for tools that specifically want
    only the recipe-row watermark advanced.
    """
    await _ensure_synced(client, cache, _MANUFACTURING_ORDER_RECIPE_ROW_SPEC)


# ---------------------------------------------------------------------------
# Force-resync (truncate + cold-start re-pull, atomically)
# ---------------------------------------------------------------------------


ENTITY_SPECS: dict[str, EntitySpec] = {
    "sales_order": _SALES_ORDER_SPEC,
    "stock_adjustment": _STOCK_ADJUSTMENT_SPEC,
    "manufacturing_order": _MANUFACTURING_ORDER_SPEC,
    "purchase_order": _PURCHASE_ORDER_SPEC,
    "stock_transfer": _STOCK_TRANSFER_SPEC,
}
"""Public registry of top-level entity specs by user-facing key.

Used by the ``rebuild_cache`` MCP tool (``cache_admin``) to look up the
cache classes and watermark keys for any cached entity type. Sibling
row specs (PO rows, MO recipe rows) aren't keyed at the top level —
they're reachable via each spec's ``related_specs`` instead.
"""


async def force_resync(
    client: KatanaClient, cache: TypedCacheEngine, entity_key: str
) -> None:
    """Atomically truncate cache tables for one entity and re-fetch from Katana.

    Holds the entity's sync lock(s) — parent plus every related spec's lock
    — across both the truncate and the cold-start re-fetch. The normal
    ``ensure_<entity>_synced`` path acquires and releases its lock once per
    sync; this helper does not, so a concurrent ``list_<entity>`` blocks on
    the same locks until the re-fetch completes and never observes the
    intermediate empty state.

    Use case: the ``rebuild_cache`` MCP tool, when phantom rows have
    accumulated in the cache (entities present locally that no longer exist
    upstream because a hard-delete or partial sync left no tombstone for
    the incremental delta to pick up).
    """
    if entity_key not in ENTITY_SPECS:
        msg = (
            f"Unknown entity_key {entity_key!r}; expected one of {sorted(ENTITY_SPECS)}"
        )
        raise ValueError(msg)
    spec = ENTITY_SPECS[entity_key]
    all_specs: tuple[EntitySpec, ...] = (spec, *spec.related_specs)

    async with AsyncExitStack() as stack:
        for s in all_specs:
            await stack.enter_async_context(cache.lock_for(s.entity_key))
        # All locks held. Truncate child tables first to satisfy FK
        # constraints, then the parent. PO/SO row-spec ``cache_cls`` is the
        # same SQLModel as ``spec.child_cls``; the set dedupes.
        children_to_delete: set[type] = set()
        if spec.child_cls is not None:
            children_to_delete.add(spec.child_cls)
        for related in spec.related_specs:
            children_to_delete.add(related.cache_cls)
        async with cache.session() as session:
            for child_cls in children_to_delete:
                await session.exec(delete(child_cls))
            await session.exec(delete(spec.cache_cls))
            for s in all_specs:
                state_row = await session.get(SyncState, s.entity_key)
                if state_row is not None:
                    await session.delete(state_row)
            await session.commit()
        # Re-fetch under the still-held locks. Parent first so its inline
        # rows (PO/SO) land before the row spec's separate fetch picks up
        # row-level tombstones the parent payload omits.
        for s in all_specs:
            await _sync_one_locked(client, cache, s)
