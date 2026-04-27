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
        CachedManufacturingOrder,
        CachedSalesOrder,
        CachedSalesOrderRow,
        CachedStockAdjustment,
        CachedStockAdjustmentRow,
        ManufacturingOrderStatus,
        SalesOrderProductionStatus,
        SalesOrderStatus,
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
    status: SalesOrderStatus | str | None = None,
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
    """Build a ``CachedSalesOrder`` for direct cache insertion.

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
        CachedSalesOrder as _CachedSalesOrder,
        SalesOrderProductionStatus as _ProductionStatus,
        SalesOrderStatus as _SalesOrderStatus,
    )

    resolved_status = (
        _SalesOrderStatus(status)
        if isinstance(status, str)
        else (status if status is not None else _SalesOrderStatus.not_shipped)
    )
    resolved_prod_status = (
        _ProductionStatus(production_status)
        if isinstance(production_status, str)
        else production_status
    )

    cached = _CachedSalesOrder(
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
    )
    # ``sales_order_rows`` is a SQLModel ``Relationship`` — set after
    # construction since the descriptor doesn't accept input via __init__.
    cached.sales_order_rows = rows if rows is not None else []
    return cached


def make_sales_order_row(
    *,
    id: int,
    sales_order_id: int,
    variant_id: int,
    quantity: float = 1.0,
    price_per_unit: float | None = None,
    linked_manufacturing_order_id: int | None = None,
) -> CachedSalesOrderRow:
    """Build a ``CachedSalesOrderRow`` for direct cache insertion."""
    from katana_public_api_client.models_pydantic._generated import (
        CachedSalesOrderRow as _CachedSalesOrderRow,
    )

    return _CachedSalesOrderRow(
        id=id,
        sales_order_id=sales_order_id,
        variant_id=variant_id,
        quantity=quantity,
        price_per_unit=price_per_unit,
        linked_manufacturing_order_id=linked_manufacturing_order_id,
    )


# ----------------------------------------------------------------------------
# stock_adjustments
# ----------------------------------------------------------------------------


def make_stock_adjustment(
    *,
    id: int = 1,
    stock_adjustment_number: str = "SA-TEST",
    location_id: int = 1,
    stock_adjustment_date: datetime | None = None,
    reason: str | None = None,
    additional_info: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    deleted_at: datetime | None = None,
    rows: list[CachedStockAdjustmentRow] | None = None,
) -> CachedStockAdjustment:
    """Build a ``CachedStockAdjustment`` for direct cache insertion.

    Same datetime-normalization contract as :func:`make_sales_order` —
    callers may pass tz-aware datetimes; the factory routes everything
    through ``naive_utc`` so cache filter comparisons work either way.
    ``created_at`` defaults to 2026-04-01 to match the sales-order builder
    so cross-entity date-window tests share a baseline.
    """
    from katana_mcp.tools.tool_result_utils import naive_utc

    from katana_public_api_client.models_pydantic._generated import (
        CachedStockAdjustment as _CachedStockAdjustment,
    )

    cached = _CachedStockAdjustment(
        id=id,
        stock_adjustment_number=stock_adjustment_number,
        location_id=location_id,
        stock_adjustment_date=naive_utc(stock_adjustment_date),
        reason=reason,
        additional_info=additional_info,
        created_at=naive_utc(created_at) or datetime(2026, 4, 1),
        updated_at=naive_utc(updated_at),
        deleted_at=naive_utc(deleted_at),
    )
    cached.stock_adjustment_rows = rows if rows is not None else []
    return cached


def make_stock_adjustment_row(
    *,
    id: int,
    stock_adjustment_id: int,
    variant_id: int,
    quantity: float = 1.0,
    cost_per_unit: float | None = None,
) -> CachedStockAdjustmentRow:
    """Build a ``CachedStockAdjustmentRow`` for direct cache insertion."""
    from katana_public_api_client.models_pydantic._generated import (
        CachedStockAdjustmentRow as _CachedStockAdjustmentRow,
    )

    return _CachedStockAdjustmentRow(
        id=id,
        stock_adjustment_id=stock_adjustment_id,
        variant_id=variant_id,
        quantity=quantity,
        cost_per_unit=cost_per_unit,
    )


# ----------------------------------------------------------------------------
# manufacturing_orders
# ----------------------------------------------------------------------------


def make_manufacturing_order(
    *,
    id: int = 1,
    order_no: str = "MO-TEST",
    status: ManufacturingOrderStatus | str | None = None,
    variant_id: int | None = 100,
    location_id: int | None = 1,
    planned_quantity: float | None = 10.0,
    actual_quantity: float | None = None,
    is_linked_to_sales_order: bool | None = False,
    sales_order_id: int | None = None,
    total_cost: float | None = None,
    order_created_date: datetime | None = None,
    production_deadline_date: datetime | None = None,
    done_date: datetime | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    deleted_at: datetime | None = None,
) -> CachedManufacturingOrder:
    """Build a ``CachedManufacturingOrder`` for direct cache insertion.

    No row table — the ``/manufacturing_orders`` list endpoint returns
    summary rows without nested children, so the cache-backed list tool
    only ever queries this single table. ``order_created_date`` and
    ``created_at`` both default to 2026-04-01 to match the other
    factories' baseline.
    """
    from katana_mcp.tools.tool_result_utils import naive_utc

    from katana_public_api_client.models_pydantic._generated import (
        CachedManufacturingOrder as _CachedManufacturingOrder,
        ManufacturingOrderStatus as _ManufacturingOrderStatus,
    )

    resolved_status = (
        _ManufacturingOrderStatus(status)
        if isinstance(status, str)
        else (status if status is not None else _ManufacturingOrderStatus.not_started)
    )

    return _CachedManufacturingOrder(
        id=id,
        order_no=order_no,
        status=resolved_status,
        variant_id=variant_id,
        location_id=location_id,
        planned_quantity=planned_quantity,
        actual_quantity=actual_quantity,
        is_linked_to_sales_order=is_linked_to_sales_order,
        sales_order_id=sales_order_id,
        total_cost=total_cost,
        order_created_date=naive_utc(order_created_date),
        production_deadline_date=naive_utc(production_deadline_date),
        done_date=naive_utc(done_date),
        created_at=naive_utc(created_at) or datetime(2026, 4, 1),
        updated_at=naive_utc(updated_at),
        deleted_at=naive_utc(deleted_at),
    )
