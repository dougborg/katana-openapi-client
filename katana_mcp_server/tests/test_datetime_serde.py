"""Wire-datetime serialization tests.

Pins the ``WireDatetime`` pydantic annotation in
``katana_mcp.tools._modification``: naive datetimes must be normalized to
UTC before they reach the Katana attrs models, otherwise Katana's RFC
3339 validator rejects the wire payload with a silent 422.

Regression: 2026-05-12 supplier PO-reconciliation session — 9 confirm clicks
silently failed because ``arrival_date="2026-06-23T00:00:00"`` (naive)
serialized as ``"2026-06-23T00:00:00"`` (no Z) and Katana refused the
PATCH. Iframe error-handling (Bug #4 in the same session) hid the
failure, compounding the debugging cost.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from katana_mcp.tools._modification import WireDatetime
from pydantic import BaseModel, ValidationError


class _Model(BaseModel):
    """Minimal model that uses the annotation under test."""

    when: WireDatetime | None = None


class TestWireDatetimeNormalization:
    def test_naive_datetime_gets_utc_tzinfo(self):
        m = _Model(when=datetime(2026, 6, 23, 12, 30, 0))
        assert m.when is not None
        assert m.when.tzinfo is UTC
        # Wire format: attrs serializers call isoformat() — confirm the
        # output carries a TZ suffix Katana will accept.
        assert m.when.isoformat() == "2026-06-23T12:30:00+00:00"

    def test_tz_aware_utc_passes_through(self):
        original = datetime(2026, 6, 23, 12, 30, 0, tzinfo=UTC)
        m = _Model(when=original)
        assert m.when == original
        # tzinfo identity preserved (not coerced to a different UTC tzinfo
        # representation).
        assert m.when is not None
        assert m.when.tzinfo is UTC

    def test_tz_aware_non_utc_preserves_offset(self):
        pst = timezone(timedelta(hours=-8))
        original = datetime(2026, 6, 23, 4, 30, 0, tzinfo=pst)
        m = _Model(when=original)
        assert m.when == original
        assert m.when is not None
        assert m.when.utcoffset() == timedelta(hours=-8)

    def test_none_passes_through(self):
        m = _Model(when=None)
        assert m.when is None

    def test_iso_string_with_z_parses_and_round_trips(self):
        # pydantic accepts ISO strings for datetime fields; ensure the
        # AfterValidator doesn't break that path.
        m = _Model.model_validate({"when": "2026-06-23T12:30:00Z"})
        assert m.when is not None
        assert m.when.tzinfo is not None
        assert m.when.utcoffset() == timedelta(0)

    def test_iso_string_without_tz_normalizes_to_utc(self):
        # The agent / caller passes a naive ISO string. Pydantic parses
        # as naive datetime; AfterValidator attaches UTC.
        m = _Model.model_validate({"when": "2026-06-23T12:30:00"})
        assert m.when is not None
        assert m.when.tzinfo is UTC

    def test_invalid_datetime_string_still_raises(self):
        with pytest.raises(ValidationError):
            _Model.model_validate({"when": "not-a-date"})

    def test_tzinfo_subclass_with_none_utcoffset_is_normalized(self):
        # A datetime can carry a non-None ``tzinfo`` whose ``utcoffset()``
        # returns ``None`` — Python's ``isoformat()`` then drops the
        # offset suffix, same failure mode as a fully-naive datetime
        # against Katana's RFC 3339 validator. The normalizer must catch
        # this too, not just ``tzinfo is None``.
        from datetime import tzinfo as TzInfoBase

        class _NullOffsetTz(TzInfoBase):
            def utcoffset(self, _dt: datetime | None) -> timedelta | None:
                return None

            def tzname(self, _dt: datetime | None) -> str | None:
                return None

            def dst(self, _dt: datetime | None) -> timedelta | None:
                return None

        weird_tz = _NullOffsetTz()
        m = _Model(when=datetime(2026, 6, 23, 12, 30, 0, tzinfo=weird_tz))
        assert m.when is not None
        # Normalized → tzinfo replaced with UTC, isoformat carries the
        # offset Katana needs.
        assert m.when.utcoffset() == timedelta(0)
        assert m.when.isoformat() == "2026-06-23T12:30:00+00:00"


class TestRealRequestModelsNormalizeNaiveDatetime:
    """End-to-end: confirm the live MCP request models normalize naive
    datetimes, so the bug-report scenario (modify_purchase_order with
    naive arrival_date) can't recur.
    """

    def test_modify_po_header_patch_normalizes_naive_arrival_date(self):
        from katana_mcp.tools.foundation.purchase_orders import POHeaderPatch

        patch = POHeaderPatch.model_validate(
            {"expected_arrival_date": "2026-06-23T00:00:00"}
        )
        assert patch.expected_arrival_date is not None
        assert patch.expected_arrival_date.tzinfo is UTC

    def test_modify_po_row_patch_normalizes_naive_arrival_date(self):
        from katana_mcp.tools.foundation.purchase_orders import PORowUpdate

        patch = PORowUpdate.model_validate(
            {"id": 1, "arrival_date": "2026-06-23T00:00:00"}
        )
        assert patch.arrival_date is not None
        assert patch.arrival_date.tzinfo is UTC

    def test_create_so_normalizes_naive_delivery_date(self):
        from katana_mcp.tools.foundation.sales_orders import (
            CreateSalesOrderRequest,
            SalesOrderItem,
        )

        req = CreateSalesOrderRequest.model_validate(
            {
                "customer_id": 1,
                "location_id": 1,
                "order_number": "SO-1",
                "delivery_date": "2026-06-23T00:00:00",
                "items": [
                    SalesOrderItem(
                        variant_id=10, quantity=1.0, price_per_unit=2.0
                    ).model_dump()
                ],
            }
        )
        assert req.delivery_date is not None
        assert req.delivery_date.tzinfo is UTC

    def test_tz_aware_non_utc_preserved_through_real_model(self):
        from katana_mcp.tools.foundation.purchase_orders import POHeaderPatch

        patch = POHeaderPatch.model_validate(
            {"expected_arrival_date": "2026-06-23T00:00:00-08:00"}
        )
        assert patch.expected_arrival_date is not None
        assert patch.expected_arrival_date.utcoffset() == timedelta(hours=-8)

    def test_create_stock_transfer_normalizes_naive_expected_arrival_date(self):
        # ``CreateStockTransferRequest.expected_arrival_date`` is a *required*
        # WireDatetime (no ``| None`` default). An earlier bulk-replace pass
        # keyed on the ``datetime | None`` pattern missed this field; the
        # tool's request builder calls ``.isoformat()`` on the value, so a
        # naive input would have serialized without a timezone offset and
        # tripped Katana's 422 RFC 3339 validator — exactly the failure
        # mode the rest of this test module is pinning. Pin this path
        # explicitly so a future regression on the required-datetime case
        # surfaces here instead of in a live session.
        from katana_mcp.tools.foundation.stock_transfers import (
            CreateStockTransferRequest,
            StockTransferRowInput,
        )

        req = CreateStockTransferRequest.model_validate(
            {
                "source_location_id": 1,
                "destination_location_id": 2,
                "expected_arrival_date": "2026-06-23T00:00:00",
                "rows": [
                    StockTransferRowInput(variant_id=10, quantity=1.0).model_dump()
                ],
            }
        )
        assert req.expected_arrival_date.tzinfo is UTC
