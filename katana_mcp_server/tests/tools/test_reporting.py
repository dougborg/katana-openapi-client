"""Tests for reporting/aggregation MCP tools."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.reporting import (
    InventoryVelocityRequest,
    SalesSummaryRequest,
    TopSellingVariantsRequest,
    _inventory_velocity_impl,
    _sales_summary_impl,
    _top_selling_variants_impl,
    inventory_velocity,
    sales_summary,
    top_selling_variants,
)

from katana_public_api_client.client_types import UNSET
from tests.conftest import create_mock_context

# ============================================================================
# Mock helpers
# ============================================================================

_SO_GET_ALL = "katana_public_api_client.api.sales_order.get_all_sales_orders"
_INV_GET_ALL = "katana_public_api_client.api.inventory.get_all_inventory_point"
_REPORTING_UNWRAP_DATA = "katana_mcp.tools.foundation.reporting.unwrap_data"


def _mock_row(
    *,
    id: int,
    variant_id: int,
    quantity: float,
    price_per_unit: float,
    total_discount: float | None = None,
) -> MagicMock:
    r = MagicMock()
    r.id = id
    r.variant_id = variant_id
    r.quantity = quantity
    r.price_per_unit = price_per_unit
    r.total_discount = total_discount if total_discount is not None else UNSET
    return r


_UNSET_CREATED_AT = object()


def _mock_so(
    *,
    id: int,
    customer_id: int = 1,
    created_at: datetime | None | object = _UNSET_CREATED_AT,
    rows: list | None = None,
) -> MagicMock:
    so = MagicMock()
    so.id = id
    so.customer_id = customer_id
    # `created_at` can be explicitly None (safety-filter will skip date check)
    # or a datetime (will be filtered against the window). Default is an
    # arbitrary in-March date used by the stable non-velocity tests.
    if created_at is _UNSET_CREATED_AT:
        so.created_at = datetime(2026, 3, 1, 9, 0, tzinfo=UTC)
    else:
        so.created_at = created_at
    so.sales_order_rows = rows or []
    return so


def _mock_inv_item(qty: float) -> MagicMock:
    item = MagicMock()
    item.quantity_in_stock = str(qty)
    item.quantity_committed = "0"
    item.quantity_expected = "0"
    return item


# ============================================================================
# top_selling_variants
# ============================================================================


@pytest.mark.asyncio
async def test_top_selling_variants_sorts_by_units_and_applies_limit():
    """Three variants, sort by units descending, limit trims to 2."""
    context, lifespan_ctx = create_mock_context()

    # Variant cache returns variant dicts for enrichment
    async def fake_get_by_id(entity_type, variant_id):
        return {
            100: {
                "id": 100,
                "sku": "BIKE-A",
                "display_name": "Bike A",
                "product_id": 10,
            },
            200: {
                "id": 200,
                "sku": "BIKE-B",
                "display_name": "Bike B",
                "product_id": 20,
            },
            300: {
                "id": 300,
                "sku": "HELMET-X",
                "display_name": "Helmet X",
                "product_id": 30,
            },
        }.get(variant_id)

    lifespan_ctx.cache.get_by_id = AsyncMock(side_effect=fake_get_by_id)

    # Three variants: BIKE-B=10u/2000, BIKE-A=5u/3000, HELMET-X=15u/450
    orders = [
        _mock_so(
            id=1,
            created_at=datetime(2026, 3, 5, tzinfo=UTC),
            rows=[
                _mock_row(id=1, variant_id=100, quantity=5, price_per_unit=600),
                _mock_row(id=2, variant_id=200, quantity=10, price_per_unit=200),
            ],
        ),
        _mock_so(
            id=2,
            created_at=datetime(2026, 3, 10, tzinfo=UTC),
            rows=[
                _mock_row(id=3, variant_id=300, quantity=15, price_per_unit=30),
            ],
        ),
    ]

    # No category lookup will succeed — no filter in this test
    request = TopSellingVariantsRequest(
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
        limit=2,
        order_by="units",
    )

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_REPORTING_UNWRAP_DATA, return_value=orders),
    ):
        result = await _top_selling_variants_impl(request, context)

    assert len(result.rows) == 2
    # HELMET-X has 15 units (highest), then BIKE-B with 10
    assert result.rows[0].sku == "HELMET-X"
    assert result.rows[0].units == 15
    assert result.rows[0].revenue == 450.0
    assert result.rows[0].order_count == 1
    assert result.rows[1].sku == "BIKE-B"
    assert result.rows[1].units == 10


@pytest.mark.asyncio
async def test_top_selling_variants_sort_by_revenue():
    """order_by='revenue' sorts by dollar volume, not units."""
    context, lifespan_ctx = create_mock_context()

    async def fake_get_by_id(entity_type, variant_id):
        return {
            100: {
                "id": 100,
                "sku": "BIKE-A",
                "display_name": "Bike A",
                "product_id": 10,
            },
            200: {
                "id": 200,
                "sku": "BIKE-B",
                "display_name": "Bike B",
                "product_id": 20,
            },
            300: {
                "id": 300,
                "sku": "HELMET-X",
                "display_name": "Helmet X",
                "product_id": 30,
            },
        }.get(variant_id)

    lifespan_ctx.cache.get_by_id = AsyncMock(side_effect=fake_get_by_id)

    orders = [
        _mock_so(
            id=1,
            rows=[
                _mock_row(id=1, variant_id=100, quantity=5, price_per_unit=600),  # 3000
                _mock_row(
                    id=2, variant_id=200, quantity=10, price_per_unit=200
                ),  # 2000
                _mock_row(id=3, variant_id=300, quantity=15, price_per_unit=30),  # 450
            ],
        ),
    ]

    request = TopSellingVariantsRequest(
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
        order_by="revenue",
    )

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_REPORTING_UNWRAP_DATA, return_value=orders),
    ):
        result = await _top_selling_variants_impl(request, context)

    assert result.rows[0].sku == "BIKE-A"
    assert result.rows[0].revenue == 3000.0
    assert result.rows[1].sku == "BIKE-B"
    assert result.rows[2].sku == "HELMET-X"


@pytest.mark.asyncio
async def test_top_selling_variants_category_filter():
    """category filter drops variants whose item category doesn't match."""
    context, lifespan_ctx = create_mock_context()

    async def fake_get_by_id(entity_type, variant_id):
        return {
            100: {
                "id": 100,
                "sku": "BIKE-A",
                "display_name": "Bike A",
                "product_id": 10,
            },
            300: {
                "id": 300,
                "sku": "HELMET-X",
                "display_name": "Helmet X",
                "product_id": 30,
            },
        }.get(variant_id)

    lifespan_ctx.cache.get_by_id = AsyncMock(side_effect=fake_get_by_id)

    # Mock the category fetcher: product_id 10 -> "bikes", product_id 30 -> "accessories"
    async def fake_fetch_category(services, product_id):
        return {10: "bikes", 30: "accessories"}.get(product_id)

    orders = [
        _mock_so(
            id=1,
            rows=[
                _mock_row(id=1, variant_id=100, quantity=5, price_per_unit=600),
                _mock_row(id=2, variant_id=300, quantity=15, price_per_unit=30),
            ],
        ),
    ]

    request = TopSellingVariantsRequest(
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
        category="bikes",
    )

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_REPORTING_UNWRAP_DATA, return_value=orders),
        patch(
            "katana_mcp.tools.foundation.reporting._fetch_category_for_product",
            side_effect=fake_fetch_category,
        ),
    ):
        result = await _top_selling_variants_impl(request, context)

    # Only BIKE-A (category=bikes) should remain
    assert len(result.rows) == 1
    assert result.rows[0].sku == "BIKE-A"


# ============================================================================
# sales_summary
# ============================================================================


@pytest.mark.asyncio
async def test_sales_summary_group_by_day_produces_row_per_day():
    """Two orders across two distinct days produces two rows, sorted by day."""
    context, _ = create_mock_context()

    orders = [
        _mock_so(
            id=1,
            created_at=datetime(2026, 3, 5, 10, 0, tzinfo=UTC),
            rows=[
                _mock_row(id=1, variant_id=100, quantity=3, price_per_unit=100),
            ],
        ),
        _mock_so(
            id=2,
            created_at=datetime(2026, 3, 6, 14, 0, tzinfo=UTC),
            rows=[
                _mock_row(id=2, variant_id=200, quantity=7, price_per_unit=50),
            ],
        ),
    ]

    request = SalesSummaryRequest(
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
        group_by="day",
    )

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_REPORTING_UNWRAP_DATA, return_value=orders),
    ):
        result = await _sales_summary_impl(request, context)

    assert len(result.rows) == 2
    assert result.rows[0].group == "2026-03-05"
    assert result.rows[0].units == 3
    assert result.rows[0].revenue == 300.0
    assert result.rows[0].order_count == 1
    assert result.rows[1].group == "2026-03-06"
    assert result.rows[1].units == 7
    assert result.rows[1].revenue == 350.0


@pytest.mark.asyncio
async def test_sales_summary_group_by_customer():
    """group_by=customer aggregates across all rows per customer."""
    context, _ = create_mock_context()

    orders = [
        _mock_so(
            id=1,
            customer_id=42,
            rows=[_mock_row(id=1, variant_id=100, quantity=2, price_per_unit=50)],
        ),
        _mock_so(
            id=2,
            customer_id=42,
            rows=[_mock_row(id=2, variant_id=200, quantity=3, price_per_unit=100)],
        ),
        _mock_so(
            id=3,
            customer_id=99,
            rows=[_mock_row(id=3, variant_id=100, quantity=5, price_per_unit=20)],
        ),
    ]

    request = SalesSummaryRequest(
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 31),
        group_by="customer",
    )

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_REPORTING_UNWRAP_DATA, return_value=orders),
    ):
        result = await _sales_summary_impl(request, context)

    # Sort by revenue descending — customer 42 has 100+300=400, 99 has 100
    assert len(result.rows) == 2
    assert result.rows[0].group == "42"
    assert result.rows[0].revenue == 400.0
    assert result.rows[0].order_count == 2
    assert result.rows[1].group == "99"
    assert result.rows[1].revenue == 100.0


# ============================================================================
# inventory_velocity
# ============================================================================


@pytest.mark.asyncio
async def test_inventory_velocity_computes_avg_daily_and_days_of_cover():
    """One variant, 180 units over 90 days, 600 stock on hand → 2u/day, 300 days cover."""
    context, lifespan_ctx = create_mock_context()

    lifespan_ctx.cache.get_by_sku = AsyncMock(
        return_value={"id": 500, "sku": "BIKE-MTB-01", "display_name": "Mountain Bike"}
    )

    # created_at=None means the safety-filter in
    # _fetch_delivered_sales_orders_in_window skips the date check, so these
    # fixtures are stable regardless of what "now" is at test time.
    orders = [
        _mock_so(
            id=1,
            created_at=None,
            rows=[_mock_row(id=1, variant_id=500, quantity=100, price_per_unit=0)],
        ),
        _mock_so(
            id=2,
            created_at=None,
            rows=[_mock_row(id=2, variant_id=500, quantity=80, price_per_unit=0)],
        ),
        # Other-variant row is ignored
        _mock_so(
            id=3,
            created_at=None,
            rows=[_mock_row(id=3, variant_id=999, quantity=50, price_per_unit=0)],
        ),
    ]

    inv_items = [_mock_inv_item(400), _mock_inv_item(200)]  # sum = 600

    request = InventoryVelocityRequest(
        sku_or_variant_id="BIKE-MTB-01",
        period_days=90,
    )

    # The inventory fetch inside _fetch_stock_on_hand uses a different
    # unwrap_data import path — patch both the reporting alias (used by
    # _fetch_delivered_sales_orders_in_window) and the inventory call site.
    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(
            f"{_INV_GET_ALL}.asyncio_detailed",
            new_callable=AsyncMock,
        ),
        patch(_REPORTING_UNWRAP_DATA, side_effect=[orders, inv_items]),
    ):
        result = await _inventory_velocity_impl(request, context)

    assert result.variant_id == 500
    assert result.sku == "BIKE-MTB-01"
    assert result.units_sold == 180
    assert result.avg_daily == pytest.approx(2.0)
    assert result.stock_on_hand == 600
    assert result.days_of_cover == pytest.approx(300.0)
    assert result.period_days == 90


@pytest.mark.asyncio
async def test_inventory_velocity_zero_sales_returns_none_cover():
    """avg_daily=0 ⇒ days_of_cover is None (no divide-by-zero)."""
    context, lifespan_ctx = create_mock_context()

    lifespan_ctx.cache.get_by_sku = AsyncMock(
        return_value={"id": 500, "sku": "DEAD-SKU", "display_name": "Unsold"}
    )

    inv_items = [_mock_inv_item(50)]

    request = InventoryVelocityRequest(
        sku_or_variant_id="DEAD-SKU",
        period_days=90,
    )

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(f"{_INV_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_REPORTING_UNWRAP_DATA, side_effect=[[], inv_items]),
    ):
        result = await _inventory_velocity_impl(request, context)

    assert result.units_sold == 0
    assert result.avg_daily == 0.0
    assert result.stock_on_hand == 50
    assert result.days_of_cover is None


# ============================================================================
# Validation
# ============================================================================


def test_top_selling_variants_rejects_limit_zero():
    """limit must be >= 1."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TopSellingVariantsRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            limit=0,
        )


def test_inventory_velocity_rejects_out_of_bounds_period():
    """period_days must be in [1, 365]."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        InventoryVelocityRequest(sku_or_variant_id="X", period_days=0)
    with pytest.raises(ValidationError):
        InventoryVelocityRequest(sku_or_variant_id="X", period_days=400)


# ============================================================================
# format=json (reporting tools)
# ============================================================================


def _content_text(result) -> str:
    return result.content[0].text


@pytest.mark.asyncio
async def test_top_selling_variants_format_json_returns_json():
    from katana_mcp.tools.foundation.reporting import TopSellingVariantsResponse

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.reporting._top_selling_variants_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = TopSellingVariantsResponse(
            rows=[],
            total_variants=0,
            window_start="2026-01-01",
            window_end="2026-01-31",
        )
        result = await top_selling_variants(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            format="json",
            context=context,
        )

    data = json.loads(_content_text(result))
    assert data["total_variants"] == 0


@pytest.mark.asyncio
async def test_sales_summary_format_json_returns_json():
    from katana_mcp.tools.foundation.reporting import SalesSummaryResponse

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.reporting._sales_summary_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = SalesSummaryResponse(
            rows=[],
            group_by="day",
            window_start="2026-01-01",
            window_end="2026-01-31",
        )
        result = await sales_summary(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            group_by="day",
            format="json",
            context=context,
        )

    data = json.loads(_content_text(result))
    assert data["group_by"] == "day"


@pytest.mark.asyncio
async def test_inventory_velocity_format_json_returns_json():
    from katana_mcp.tools.foundation.reporting import VelocityStats

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.reporting._inventory_velocity_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = VelocityStats(
            sku="V-1",
            variant_id=1,
            units_sold=5.0,
            avg_daily=0.5,
            stock_on_hand=10,
            days_of_cover=20.0,
            period_days=10,
            window_start="2026-01-01",
            window_end="2026-01-10",
        )
        result = await inventory_velocity(
            sku_or_variant_id="V-1",
            period_days=10,
            format="json",
            context=context,
        )

    data = json.loads(_content_text(result))
    assert data["variant_id"] == 1
    assert data["units_sold"] == 5.0
