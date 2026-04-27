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

from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.api.stock_adjustment import get_all_stock_adjustments
from katana_public_api_client.models_pydantic._generated import (
    CachedSalesOrder,
    CachedSalesOrderRow,
    CachedStockAdjustment,
    CachedStockAdjustmentRow,
    SalesOrder as PydanticSalesOrder,
    StockAdjustment as PydanticStockAdjustment,
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
