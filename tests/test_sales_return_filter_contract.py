"""Generated wire keys for the verified sales-return filters (#939)."""

from __future__ import annotations

from datetime import UTC, datetime

from katana_public_api_client.api.sales_return import get_all_sales_returns


def test_sales_return_filters_use_live_wire_keys() -> None:
    params = get_all_sales_returns._get_kwargs(
        order_no="SDT-RETURN-001",
        return_location_id=123,
        order_return_date_min=datetime(2026, 9, 19, tzinfo=UTC),
    )["params"]

    assert params == {
        "order_no": "SDT-RETURN-001",
        "return_location_id": 123,
        "order_return_date_min": "2026-09-19T00:00:00+00:00",
    }
