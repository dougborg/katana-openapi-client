"""Per-entity cache sync against the Katana API.

Each ``ensure_<entity>_synced`` helper:
1. Takes the entity's lock to serialize concurrent sync calls.
2. Reads the ``SyncState`` watermark and passes it to the API as
   ``updated_at_min`` so only changed rows come back on subsequent calls.
3. Converts attrs API objects to SQLModel rows via ``from_attrs()``.
4. Upserts rows and advances the watermark, all in one session.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.models_pydantic._generated import (
    SalesOrder as PydanticSalesOrder,
)
from katana_public_api_client.utils import unwrap_data

from .sync_state import SyncState

if TYPE_CHECKING:
    from katana_public_api_client import KatanaClient

    from .engine import TypedCacheEngine


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

        rows = [PydanticSalesOrder.from_attrs(ao) for ao in attrs_orders]

        async with cache.session() as session:
            for row in rows:
                await session.merge(row)
            # SQLite's DateTime column doesn't preserve tzinfo, so naive
            # UTC on the write side. ``row_count`` is the last-fetch size
            # (not a cumulative total, which would drift since ``rows``
            # includes re-sync duplicates); consumers needing a true
            # total run ``SELECT COUNT(*)`` on the entity table itself.
            await session.merge(
                SyncState(
                    entity_type="sales_order",
                    last_synced=datetime.now(tz=UTC).replace(tzinfo=None),
                    row_count=len(rows),
                )
            )
            await session.commit()
