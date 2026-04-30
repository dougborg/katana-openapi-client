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
from typing import Any

from katana_mcp.tools.tool_result_utils import naive_utc
from katana_mcp.typed_cache import TypedCacheEngine

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
    ManufacturingOrderStatus,
    PurchaseOrderEntityType,
    PurchaseOrderStatus,
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

    resolved_status = (
        SalesOrderStatus(status)
        if isinstance(status, str)
        else (status if status is not None else SalesOrderStatus.not_shipped)
    )
    resolved_prod_status = (
        SalesOrderProductionStatus(production_status)
        if isinstance(production_status, str)
        else production_status
    )

    cached = CachedSalesOrder(
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
    return CachedSalesOrderRow(
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

    cached = CachedStockAdjustment(
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
    return CachedStockAdjustmentRow(
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
    order_no: str | None = "MO-TEST",
    status: ManufacturingOrderStatus | str | None = None,
    ingredient_availability: str | None = None,
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

    resolved_status = (
        ManufacturingOrderStatus(status)
        if isinstance(status, str)
        else (status if status is not None else ManufacturingOrderStatus.not_started)
    )

    from katana_public_api_client.models_pydantic._generated import (
        OutsourcedPurchaseOrderIngredientAvailability,
    )

    resolved_ingredient_availability = (
        OutsourcedPurchaseOrderIngredientAvailability(ingredient_availability)
        if ingredient_availability is not None
        else None
    )

    return CachedManufacturingOrder(
        id=id,
        order_no=order_no,
        status=resolved_status,
        ingredient_availability=resolved_ingredient_availability,
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


def make_manufacturing_order_recipe_row(
    *,
    id: int,
    manufacturing_order_id: int,
    variant_id: int,
    planned_quantity_per_unit: float | None = None,
    total_actual_quantity: float | None = None,
    total_consumed_quantity: float | None = None,
    total_remaining_quantity: float | None = None,
    cost: float | None = None,
    ingredient_availability: str | None = None,
    ingredient_expected_date: datetime | None = None,
    deleted_at: datetime | None = None,
) -> CachedManufacturingOrderRecipeRow:
    """Build a ``CachedManufacturingOrderRecipeRow`` for direct cache insertion.

    Mirrors :func:`make_stock_adjustment_row`'s shape — the row carries an
    FK back to its parent ``CachedManufacturingOrder.id`` via
    ``manufacturing_order_id``. Use alongside :func:`make_manufacturing_order`
    to build parent-child fixtures for tools that join MOs to recipe rows
    (e.g., ``inventory_velocity``'s MO-consumption path,
    ``list_blocking_ingredients``'s availability rollup).
    """
    from katana_public_api_client.models_pydantic._generated import (
        OutsourcedPurchaseOrderIngredientAvailability,
    )

    resolved_availability = (
        OutsourcedPurchaseOrderIngredientAvailability(ingredient_availability)
        if ingredient_availability is not None
        else None
    )

    return CachedManufacturingOrderRecipeRow(
        id=id,
        manufacturing_order_id=manufacturing_order_id,
        variant_id=variant_id,
        planned_quantity_per_unit=planned_quantity_per_unit,
        total_actual_quantity=total_actual_quantity,
        total_consumed_quantity=total_consumed_quantity,
        total_remaining_quantity=total_remaining_quantity,
        cost=cost,
        ingredient_availability=resolved_availability,
        ingredient_expected_date=naive_utc(ingredient_expected_date),
        deleted_at=naive_utc(deleted_at),
    )


# ----------------------------------------------------------------------------
# purchase_orders
# ----------------------------------------------------------------------------


def make_purchase_order(
    *,
    id: int = 1,
    order_no: str = "PO-TEST",
    entity_type: PurchaseOrderEntityType | str = "regular",
    status: PurchaseOrderStatus | str | None = None,
    billing_status: str | None = None,
    supplier_id: int | None = 4001,
    location_id: int | None = 1,
    tracking_location_id: int | None = None,
    currency: str | None = "USD",
    expected_arrival_date: datetime | None = None,
    order_created_date: datetime | None = None,
    total: float | None = 100.0,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    deleted_at: datetime | None = None,
    rows: list[CachedPurchaseOrderRow] | None = None,
) -> CachedPurchaseOrder:
    """Build a ``CachedPurchaseOrder`` for direct cache insertion.

    Same datetime-normalization contract as :func:`make_sales_order`. The
    ``entity_type`` discriminator defaults to ``"regular"`` so tests that
    don't care about the regular/outsourced split still build valid rows;
    pass ``"outsourced"`` plus a ``tracking_location_id`` for outsourced
    fixtures.
    """

    resolved_entity_type = (
        PurchaseOrderEntityType(entity_type)
        if isinstance(entity_type, str)
        else entity_type
    )
    resolved_status = (
        PurchaseOrderStatus(status)
        if isinstance(status, str)
        else (status if status is not None else PurchaseOrderStatus.not_received)
    )

    cached = CachedPurchaseOrder(
        id=id,
        order_no=order_no,
        entity_type=resolved_entity_type,
        status=resolved_status,
        billing_status=billing_status,
        supplier_id=supplier_id,
        location_id=location_id,
        tracking_location_id=tracking_location_id,
        currency=currency,
        expected_arrival_date=naive_utc(expected_arrival_date),
        order_created_date=naive_utc(order_created_date),
        total=total,
        created_at=naive_utc(created_at) or datetime(2026, 4, 1),
        updated_at=naive_utc(updated_at),
        deleted_at=naive_utc(deleted_at),
    )
    cached.purchase_order_rows = rows if rows is not None else []
    return cached


def make_purchase_order_row(
    *,
    id: int,
    purchase_order_id: int,
    variant_id: int,
    quantity: float = 1.0,
    price_per_unit: float | None = None,
    arrival_date: datetime | None = None,
    received_date: datetime | None = None,
    total: float | None = None,
) -> CachedPurchaseOrderRow:
    """Build a ``CachedPurchaseOrderRow`` for direct cache insertion."""

    return CachedPurchaseOrderRow(
        id=id,
        purchase_order_id=purchase_order_id,
        variant_id=variant_id,
        quantity=quantity,
        price_per_unit=price_per_unit,
        arrival_date=naive_utc(arrival_date),
        received_date=naive_utc(received_date),
        total=total,
    )


# ----------------------------------------------------------------------------
# stock_transfers
# ----------------------------------------------------------------------------


def make_stock_transfer(
    *,
    id: int = 1,
    stock_transfer_number: str = "ST-TEST",
    source_location_id: int = 1,
    target_location_id: int = 2,
    status: str | None = "pending",
    transfer_date: datetime | None = None,
    order_created_date: datetime | None = None,
    expected_arrival_date: datetime | None = None,
    additional_info: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    deleted_at: datetime | None = None,
    rows: list[CachedStockTransferRow] | None = None,
) -> CachedStockTransfer:
    """Build a ``CachedStockTransfer`` for direct cache insertion.

    ``status`` is stored on the cache row as ``str | None`` (the OpenAPI
    spec types it that way; Katana returns lowercase enum values). Pass
    raw lowercase strings here — that matches what real API rows carry.
    """

    cached = CachedStockTransfer(
        id=id,
        stock_transfer_number=stock_transfer_number,
        source_location_id=source_location_id,
        target_location_id=target_location_id,
        status=status,
        transfer_date=naive_utc(transfer_date),
        order_created_date=naive_utc(order_created_date),
        expected_arrival_date=naive_utc(expected_arrival_date),
        additional_info=additional_info,
        created_at=naive_utc(created_at) or datetime(2026, 4, 1),
        updated_at=naive_utc(updated_at),
        deleted_at=naive_utc(deleted_at),
    )
    cached.stock_transfer_rows = rows if rows is not None else []
    return cached


def make_stock_transfer_row(
    *,
    id: int,
    stock_transfer_id: int,
    variant_id: int,
    quantity: float = 1.0,
    cost_per_unit: float | None = None,
) -> CachedStockTransferRow:
    """Build a ``CachedStockTransferRow`` for direct cache insertion."""
    return CachedStockTransferRow(
        id=id,
        stock_transfer_id=stock_transfer_id,
        variant_id=variant_id,
        quantity=quantity,
        cost_per_unit=cost_per_unit,
    )
