"""Per-entity cache sync against the Katana API.

Each ``ensure_<entity>_synced`` helper:
1. Takes the entity's lock to serialize concurrent sync calls.
2. Reads the ``SyncState`` watermark and passes it to the API as
   ``updated_at_min`` so only changed rows come back on subsequent calls.
3. Converts attrs API objects to ``Cached<Entity>`` SQLModel rows via the
   API pydantic class as an intermediary (so nested-row conversion stays
   in one well-tested place), then re-validates into the cache sibling.
4. Upserts parent + child rows and advances the watermark, all in one
   session.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from katana_public_api_client.api.manufacturing_order import (
    get_all_manufacturing_orders,
)
from katana_public_api_client.api.purchase_order import find_purchase_orders
from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.api.stock_adjustment import get_all_stock_adjustments
from katana_public_api_client.api.stock_transfer import get_all_stock_transfers
from katana_public_api_client.models_pydantic._generated import (
    CachedManufacturingOrder,
    CachedPurchaseOrder,
    CachedPurchaseOrderRow,
    CachedSalesOrder,
    CachedSalesOrderRow,
    CachedStockAdjustment,
    CachedStockAdjustmentRow,
    CachedStockTransfer,
    CachedStockTransferRow,
    ManufacturingOrder as PydanticManufacturingOrder,
    PurchaseOrderBase as PydanticPurchaseOrderBase,
    SalesOrder as PydanticSalesOrder,
    StockAdjustment as PydanticStockAdjustment,
    StockTransfer as PydanticStockTransfer,
)
from katana_public_api_client.utils import unwrap_data

from .sync_state import SyncState

if TYPE_CHECKING:
    from katana_public_api_client import KatanaClient

    from .engine import TypedCacheEngine


def _attrs_sales_order_to_cached(
    attrs_so: object,
) -> tuple[CachedSalesOrder, list[CachedSalesOrderRow]]:
    """Convert one attrs ``SalesOrder`` to a parent ``CachedSalesOrder`` plus
    a flat list of ``CachedSalesOrderRow`` children with explicit FKs.

    Two-step:
    1. ``PydanticSalesOrder.from_attrs`` handles UNSET → None, enum
       extraction, datetime coercion, and the registry-driven nested
       conversion of each row. The result is the API pydantic model.
    2. ``model_dump`` exports a plain dict; ``CachedSalesOrder.model_validate``
       reconstructs the parent (excluding the ``sales_order_rows``
       relationship — SQLModel ``Relationship`` descriptors don't accept
       input via ``__init__``/``model_validate``). Children are re-built as
       ``CachedSalesOrderRow`` with ``sales_order_id`` set explicitly so
       SQLAlchemy can wire the parent→child link on insert. The caller
       merges parents and children in separate passes.
    """
    api_so = PydanticSalesOrder.from_attrs(attrs_so)
    parent_data = api_so.model_dump(exclude={"sales_order_rows"})
    cached_parent = CachedSalesOrder.model_validate(parent_data)

    child_rows: list[CachedSalesOrderRow] = []
    api_rows = api_so.sales_order_rows or []
    for api_row in api_rows:
        row_data = api_row.model_dump()
        # The API model carries ``sales_order_id`` natively (Katana returns
        # it on rows). Re-asserting from the parent guards against the
        # response shape silently changing.
        row_data["sales_order_id"] = api_so.id
        child_rows.append(CachedSalesOrderRow.model_validate(row_data))
    return cached_parent, child_rows


async def ensure_sales_orders_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated sales orders from Katana and upsert into the typed cache.

    The first call on a cold cache does a full history fetch (cost scales
    with the shop's order count); subsequent calls pass
    ``updated_at_min=<last_synced>`` and typically return zero rows. The
    per-entity lock guarantees only one sync runs at a time even if
    multiple tool calls land concurrently.
    """
    async with cache.lock_for("sales_order"):
        async with cache.session() as session:
            state = await session.get(SyncState, "sales_order")
            last_synced = state.last_synced if state is not None else None

        # ``last_synced`` is persisted as naive UTC (SQLite's default
        # DateTime column strips tzinfo). Re-attach UTC before sending to
        # the API so the generated client serializes an explicit offset —
        # matches the legacy cache_sync watermark handling.
        kwargs = (
            {"updated_at_min": last_synced.replace(tzinfo=UTC)}
            if last_synced is not None
            else {}
        )
        response = await get_all_sales_orders.asyncio_detailed(client=client, **kwargs)
        attrs_orders = unwrap_data(response, default=[])

        cached_parents: list[CachedSalesOrder] = []
        cached_children: list[CachedSalesOrderRow] = []
        for attrs_so in attrs_orders:
            parent, children = _attrs_sales_order_to_cached(attrs_so)
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
            # (not a cumulative total, which would drift since ``rows``
            # includes re-sync duplicates); consumers needing a true
            # total run ``SELECT COUNT(*)`` on the entity table itself.
            await session.merge(
                SyncState(
                    entity_type="sales_order",
                    last_synced=datetime.now(tz=UTC).replace(tzinfo=None),
                    row_count=len(cached_parents),
                )
            )
            await session.commit()


def _attrs_stock_adjustment_to_cached(
    attrs_sa: object,
) -> tuple[CachedStockAdjustment, list[CachedStockAdjustmentRow]]:
    """Convert one attrs ``StockAdjustment`` to a parent + children pair.

    Same shape as :func:`_attrs_sales_order_to_cached`, with one twist:
    Katana doesn't return ``stock_adjustment_id`` on ``StockAdjustmentRow``
    (rows are nested under the parent on the wire), so the cached row's
    FK is set explicitly from the parent's ``id`` instead of being copied
    from the API response.
    """
    api_sa = PydanticStockAdjustment.from_attrs(attrs_sa)
    parent_data = api_sa.model_dump(exclude={"stock_adjustment_rows"})
    cached_parent = CachedStockAdjustment.model_validate(parent_data)

    child_rows: list[CachedStockAdjustmentRow] = []
    api_rows = api_sa.stock_adjustment_rows or []
    for api_row in api_rows:
        row_data = api_row.model_dump()
        row_data["stock_adjustment_id"] = api_sa.id
        child_rows.append(CachedStockAdjustmentRow.model_validate(row_data))
    return cached_parent, child_rows


async def ensure_stock_adjustments_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated stock adjustments from Katana and upsert into the cache.

    Mirror of :func:`ensure_sales_orders_synced` for the ``StockAdjustment``
    entity. Cold-start fetches the full history; subsequent calls pass
    ``updated_at_min`` and pick up only changed rows. Per-entity lock
    serializes concurrent calls to keep cold-start fan-out single-flight.
    """
    async with cache.lock_for("stock_adjustment"):
        async with cache.session() as session:
            state = await session.get(SyncState, "stock_adjustment")
            last_synced = state.last_synced if state is not None else None

        kwargs = (
            {"updated_at_min": last_synced.replace(tzinfo=UTC)}
            if last_synced is not None
            else {}
        )
        response = await get_all_stock_adjustments.asyncio_detailed(
            client=client, **kwargs
        )
        attrs_adjustments = unwrap_data(response, default=[])

        cached_parents: list[CachedStockAdjustment] = []
        cached_children: list[CachedStockAdjustmentRow] = []
        for attrs_sa in attrs_adjustments:
            parent, children = _attrs_stock_adjustment_to_cached(attrs_sa)
            cached_parents.append(parent)
            cached_children.extend(children)

        async with cache.session() as session:
            for parent in cached_parents:
                await session.merge(parent)
            for child in cached_children:
                await session.merge(child)
            await session.merge(
                SyncState(
                    entity_type="stock_adjustment",
                    last_synced=datetime.now(tz=UTC).replace(tzinfo=None),
                    row_count=len(cached_parents),
                )
            )
            await session.commit()


def _attrs_manufacturing_order_to_cached(
    attrs_mo: object,
) -> CachedManufacturingOrder:
    """Convert one attrs ``ManufacturingOrder`` to a ``CachedManufacturingOrder``.

    Simpler than the sales-order / stock-adjustment converters: the
    ``/manufacturing_orders`` list endpoint returns summary objects with
    no nested rows (recipe rows live at ``/manufacturing_order_recipe_rows``
    and aren't cached here), so there's only one entity to build per row.
    JSON-typed list fields (``batch_transactions``, ``serial_numbers``)
    survive ``model_dump`` as plain dict lists and ``model_validate``
    routes them into the cache class's JSON column unchanged.
    """
    api_mo = PydanticManufacturingOrder.from_attrs(attrs_mo)
    return CachedManufacturingOrder.model_validate(api_mo.model_dump())


async def ensure_manufacturing_orders_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated manufacturing orders from Katana and upsert into the cache.

    Mirror of :func:`ensure_sales_orders_synced` for the ``ManufacturingOrder``
    entity. Cold-start fetches the full history; subsequent calls pass
    ``updated_at_min`` and pick up only changed rows. Per-entity lock
    serializes concurrent calls to keep cold-start fan-out single-flight.
    """
    async with cache.lock_for("manufacturing_order"):
        async with cache.session() as session:
            state = await session.get(SyncState, "manufacturing_order")
            last_synced = state.last_synced if state is not None else None

        kwargs = (
            {"updated_at_min": last_synced.replace(tzinfo=UTC)}
            if last_synced is not None
            else {}
        )
        response = await get_all_manufacturing_orders.asyncio_detailed(
            client=client, **kwargs
        )
        attrs_orders = unwrap_data(response, default=[])

        cached_orders = [
            _attrs_manufacturing_order_to_cached(mo) for mo in attrs_orders
        ]

        async with cache.session() as session:
            for order in cached_orders:
                await session.merge(order)
            await session.merge(
                SyncState(
                    entity_type="manufacturing_order",
                    last_synced=datetime.now(tz=UTC).replace(tzinfo=None),
                    row_count=len(cached_orders),
                )
            )
            await session.commit()


def _attrs_purchase_order_to_cached(
    attrs_po: object,
) -> tuple[CachedPurchaseOrder, list[CachedPurchaseOrderRow]]:
    """Convert one attrs ``PurchaseOrder`` (regular | outsourced) to cache rows.

    Three-step:
    1. Pick the right API pydantic class from the attrs subtype: regular
       and outsourced POs share ``PurchaseOrderBase`` fields but differ in
       ``entity_type`` literal and the outsourced-only
       ``tracking_location_id`` / ``ingredient_*`` fields.
    2. Dump the API model and re-validate into ``CachedPurchaseOrder`` —
       the cache class shadows ``PurchaseOrderBase`` (renamed via
       ``CACHE_TABLE_RENAMES``) and carries an extra
       ``tracking_location_id`` column hoisted from the outsourced
       subclass via ``CACHE_EXTRA_FIELDS``. The dump captures it
       automatically when the source is an outsourced PO.
    3. Build child rows with ``purchase_order_id`` set explicitly from the
       parent, mirroring the stock-adjustment shape.
    """
    # Dispatch by attrs class via the model registry so we round-trip the
    # right subclass (regular/outsourced) — calling
    # ``PydanticPurchaseOrderBase.from_attrs`` directly would lose the
    # outsourced-only fields (``tracking_location_id`` etc.).
    from katana_public_api_client.models_pydantic._registry import get_pydantic_class

    api_class = get_pydantic_class(type(attrs_po))
    if api_class is None:
        msg = (
            f"No pydantic class registered for attrs purchase order "
            f"type {type(attrs_po).__name__}"
        )
        raise RuntimeError(msg)
    api_po: PydanticPurchaseOrderBase = api_class.from_attrs(attrs_po)

    parent_data = api_po.model_dump(exclude={"purchase_order_rows"})
    cached_parent = CachedPurchaseOrder.model_validate(parent_data)

    child_rows: list[CachedPurchaseOrderRow] = []
    api_rows = api_po.purchase_order_rows or []
    for api_row in api_rows:
        row_data = api_row.model_dump()
        # Re-assert from the parent. Katana already returns
        # ``purchase_order_id`` on rows, but the parent's id is the
        # source of truth on insert.
        row_data["purchase_order_id"] = api_po.id
        child_rows.append(CachedPurchaseOrderRow.model_validate(row_data))
    return cached_parent, child_rows


async def ensure_purchase_orders_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated purchase orders from Katana and upsert into the cache.

    Mirror of :func:`ensure_sales_orders_synced` for the ``PurchaseOrder``
    discriminated-union entity. Cold-start fetches full history; subsequent
    calls pass ``updated_at_min``. Per-entity lock keeps cold-start fan-out
    single-flight.
    """
    async with cache.lock_for("purchase_order"):
        async with cache.session() as session:
            state = await session.get(SyncState, "purchase_order")
            last_synced = state.last_synced if state is not None else None

        kwargs = (
            {"updated_at_min": last_synced.replace(tzinfo=UTC)}
            if last_synced is not None
            else {}
        )
        response = await find_purchase_orders.asyncio_detailed(client=client, **kwargs)
        attrs_orders = unwrap_data(response, default=[])

        cached_parents: list[CachedPurchaseOrder] = []
        cached_children: list[CachedPurchaseOrderRow] = []
        for attrs_po in attrs_orders:
            parent, children = _attrs_purchase_order_to_cached(attrs_po)
            cached_parents.append(parent)
            cached_children.extend(children)

        async with cache.session() as session:
            for parent in cached_parents:
                await session.merge(parent)
            for child in cached_children:
                await session.merge(child)
            await session.merge(
                SyncState(
                    entity_type="purchase_order",
                    last_synced=datetime.now(tz=UTC).replace(tzinfo=None),
                    row_count=len(cached_parents),
                )
            )
            await session.commit()


def _attrs_stock_transfer_to_cached(
    attrs_st: object,
) -> tuple[CachedStockTransfer, list[CachedStockTransferRow]]:
    """Convert one attrs ``StockTransfer`` to a cache parent + child rows.

    ``StockTransferRow`` doesn't carry a parent FK on the wire (rows
    nested under the parent in API responses), so the cache populates
    ``stock_transfer_id`` from the parent's ``id`` on insert. Mirrors the
    stock-adjustment converter's shape.
    """
    api_st = PydanticStockTransfer.from_attrs(attrs_st)
    parent_data = api_st.model_dump(exclude={"stock_transfer_rows"})
    cached_parent = CachedStockTransfer.model_validate(parent_data)

    child_rows: list[CachedStockTransferRow] = []
    api_rows = api_st.stock_transfer_rows or []
    for api_row in api_rows:
        row_data = api_row.model_dump()
        row_data["stock_transfer_id"] = api_st.id
        child_rows.append(CachedStockTransferRow.model_validate(row_data))
    return cached_parent, child_rows


async def ensure_stock_transfers_synced(
    client: KatanaClient, cache: TypedCacheEngine
) -> None:
    """Pull updated stock transfers from Katana and upsert into the cache.

    Mirror of :func:`ensure_sales_orders_synced` for the ``StockTransfer``
    entity. Cold-start fetches the full history; subsequent calls pass
    ``updated_at_min`` and pick up only changed rows. Per-entity lock
    serializes concurrent calls to keep cold-start fan-out single-flight.
    """
    async with cache.lock_for("stock_transfer"):
        async with cache.session() as session:
            state = await session.get(SyncState, "stock_transfer")
            last_synced = state.last_synced if state is not None else None

        kwargs = (
            {"updated_at_min": last_synced.replace(tzinfo=UTC)}
            if last_synced is not None
            else {}
        )
        response = await get_all_stock_transfers.asyncio_detailed(
            client=client, **kwargs
        )
        attrs_transfers = unwrap_data(response, default=[])

        cached_parents: list[CachedStockTransfer] = []
        cached_children: list[CachedStockTransferRow] = []
        for attrs_st in attrs_transfers:
            parent, children = _attrs_stock_transfer_to_cached(attrs_st)
            cached_parents.append(parent)
            cached_children.extend(children)

        async with cache.session() as session:
            for parent in cached_parents:
                await session.merge(parent)
            for child in cached_children:
                await session.merge(child)
            await session.merge(
                SyncState(
                    entity_type="stock_transfer",
                    last_synced=datetime.now(tz=UTC).replace(tzinfo=None),
                    row_count=len(cached_parents),
                )
            )
            await session.commit()
