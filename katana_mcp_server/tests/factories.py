"""Builders for SQLModel typed-cache rows used in tool tests.

Cache-backed list tools (post-#342, ADR-0018) query directly against the
typed cache instead of the live API, so tool tests pre-populate the cache
with SQLModel rows and assert on the query results. Each factory returns
a fully-constructed ``Cached<Entity>`` instance ready for insertion via
``seed_cache`` — tests don't have to remember the tz-naive-datetime rule,
default statuses, or required relationships. As new entities migrate to
cache-back (#376/#377/#378/#379), add their builders here so all five
migrations share one set of helpers.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from katana_mcp.typed_cache import TypedCacheEngine

    from katana_public_api_client.models_pydantic._generated import (
        SalesOrder as CachedSalesOrder,
        SalesOrderProductionStatus,
        SalesOrderRow as CachedSalesOrderRow,
        SalesOrderStatus as CachedSalesOrderStatus,
    )


async def seed_cache(typed_cache: TypedCacheEngine, entities: Iterable[Any]) -> None:
    """Insert pre-built SQLModel rows into the typed cache.

    Entity-agnostic bulk-add — pass an iterable of ``Cached<Entity>``
    instances built by the per-entity factories below. Commits once at
    the end so all rows land atomically.
    """
    async with typed_cache.session() as session:
        for entity in entities:
            session.add(entity)
        await session.commit()


# ----------------------------------------------------------------------------
# sales_orders
# ----------------------------------------------------------------------------


def make_sales_order(
    *,
    id: int = 1,
    order_no: str = "SO-TEST",
    customer_id: int = 42,
    location_id: int = 1,
    status: CachedSalesOrderStatus | str | None = None,
    production_status: SalesOrderProductionStatus | str | None = "NONE",
    invoicing_status: str | None = None,
    created_at: datetime | None = None,
    delivery_date: datetime | None = None,
    updated_at: datetime | None = None,
    total: float | None = 999.0,
    currency: str | None = "USD",
    deleted_at: datetime | None = None,
    rows: list[CachedSalesOrderRow] | None = None,
) -> CachedSalesOrder:
    """Build a SQLModel ``SalesOrder`` for direct cache insertion.

    Datetime args are normalized to naive UTC (the typed cache stores
    timestamps without tzinfo — SQLite's default ``DateTime`` column
    doesn't preserve offsets, so filter comparisons require naive values
    on both sides). Tz-aware inputs are converted via ``naive_utc`` so
    the factory enforces the cache's contract; callers can pass either
    flavor without breaking later comparisons. ``created_at`` defaults
    to 2026-04-01 so date-window filter tests have a stable reference.
    """
    from katana_mcp.tools.tool_result_utils import naive_utc

    from katana_public_api_client.models_pydantic._generated import (
        SalesOrder as CachedSalesOrder,
        SalesOrderProductionStatus as _ProductionStatus,
        SalesOrderStatus as CachedSalesOrderStatus,
    )

    resolved_status = (
        CachedSalesOrderStatus(status)
        if isinstance(status, str)
        else (status if status is not None else CachedSalesOrderStatus.not_shipped)
    )
    resolved_prod_status = (
        _ProductionStatus(production_status)
        if isinstance(production_status, str)
        else production_status
    )

    return CachedSalesOrder(
        id=id,
        order_no=order_no,
        customer_id=customer_id,
        location_id=location_id,
        status=resolved_status,
        production_status=resolved_prod_status,
        invoicing_status=invoicing_status,
        created_at=naive_utc(created_at) or datetime(2026, 4, 1),
        updated_at=naive_utc(updated_at),
        delivery_date=naive_utc(delivery_date),
        total=total,
        currency=currency,
        deleted_at=naive_utc(deleted_at),
        sales_order_rows=rows if rows is not None else [],
    )


def make_sales_order_row(
    *,
    id: int,
    sales_order_id: int,
    variant_id: int,
    quantity: float = 1.0,
    price_per_unit: float | None = None,
    linked_manufacturing_order_id: int | None = None,
) -> CachedSalesOrderRow:
    """Build a SQLModel ``SalesOrderRow`` for direct cache insertion."""
    from katana_public_api_client.models_pydantic._generated import (
        SalesOrderRow as CachedSalesOrderRow,
    )

    return CachedSalesOrderRow(
        id=id,
        sales_order_id=sales_order_id,
        variant_id=variant_id,
        quantity=quantity,
        price_per_unit=price_per_unit,
        linked_manufacturing_order_id=linked_manufacturing_order_id,
    )
