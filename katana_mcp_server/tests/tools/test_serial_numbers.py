"""Tests for serial-number MCP tools.

Covers the three-tool surface:
- add_serial_numbers (preview + apply, mint vs. transfer semantics, partial failure)
- list_serial_numbers (filters, paging)
- delete_serial_numbers (preview + apply, idempotency caveat)
"""

from __future__ import annotations

import datetime as _datetime
import json
from http import HTTPStatus
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.serial_numbers import (
    AddSerialNumbersRequest,
    DeleteSerialNumbersRequest,
    ListSerialNumbersRequest,
    _add_serial_numbers_impl,
    _delete_serial_numbers_impl,
    _list_serial_numbers_impl,
    register_tools,
)
from katana_mcp_server.tests.conftest import create_mock_context

from katana_public_api_client.client_types import UNSET, Response, Unset
from katana_public_api_client.models import (
    CreateSerialNumberFailedItem,
    CreateSerialNumberFailureReason,
    CreateSerialNumbersResponse,
    SerialNumber,
    SerialNumberListResponse,
    SerialNumberResourceType,
)

_SN_CREATE = "katana_public_api_client.api.serial_number.create_serial_numbers"
_SN_DELETE = "katana_public_api_client.api.serial_number.delete_serial_numbers"
_SN_LIST = "katana_public_api_client.api.serial_number.get_all_serial_numbers"


# ============================================================================
# Helpers
# ============================================================================


def _wrap_response(parsed: Any, status: int = 200) -> Response[Any]:
    """Build a Response[T] for unwrap_as to consume."""
    return Response(
        status_code=HTTPStatus(status),
        content=b"",
        headers={},
        parsed=parsed,
    )


def _make_serial_number(
    *,
    id: int = 1001,
    serial_number: str = "TEST-001",
    resource_type: SerialNumberResourceType = SerialNumberResourceType.MANUFACTURINGORDER,
    resource_id: int | None | Unset = 100,
    transaction_id: str | None | Unset = "txn-1",
    transaction_date: _datetime.datetime | None | Unset = UNSET,
    quantity_change: int = 0,
) -> SerialNumber:
    """Build an attrs SerialNumber for tests.

    ``None`` and ``UNSET`` are distinct: pass ``None`` to surface a
    field present on the wire as ``null`` (the transfer-response
    quirk for ``resource_id`` / ``transaction_id``); pass ``UNSET``
    when the field should be absent from the wire entirely. The
    helper does not coerce between them.
    """
    return SerialNumber(
        id=id,
        serial_number=serial_number,
        resource_type=resource_type,
        resource_id=resource_id,
        transaction_id=transaction_id,
        transaction_date=transaction_date,
        quantity_change=quantity_change,
    )


# ============================================================================
# add_serial_numbers — preview path
# ============================================================================


@pytest.mark.asyncio
async def test_add_serial_numbers_preview_mint_does_not_call_api():
    """preview=True for a mint type returns the plan without calling Katana."""
    context, _ = create_mock_context()
    request = AddSerialNumbersRequest(
        resource_type="ManufacturingOrder",
        resource_id=42,
        serial_numbers=["SN1", "SN2"],
        preview=True,
    )
    with patch(f"{_SN_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api:
        response = await _add_serial_numbers_impl(request, context)

    mock_api.assert_not_called()
    assert response.is_preview is True
    assert response.semantic == "mint"
    assert response.created == []
    assert response.failed == []
    assert "Preview" in response.message


@pytest.mark.asyncio
async def test_add_serial_numbers_preview_transfer_surfaces_warning():
    """preview=True for a transfer type includes the MISSING-failure warning."""
    context, _ = create_mock_context()
    request = AddSerialNumbersRequest(
        resource_type="SalesOrderRow",
        resource_id=99,
        serial_numbers=["SN1"],
        preview=True,
    )
    response = await _add_serial_numbers_impl(request, context)
    assert response.semantic == "transfer"
    assert any("Transfer semantic" in w for w in response.warnings)


# ============================================================================
# add_serial_numbers — happy paths
# ============================================================================


@pytest.mark.asyncio
async def test_add_serial_numbers_mint_mo_success():
    """Apply against ManufacturingOrder returns the created serial numbers."""
    context, _ = create_mock_context()
    sn1 = _make_serial_number(id=1001, serial_number="MO-SN-1", resource_id=42)
    sn2 = _make_serial_number(id=1002, serial_number="MO-SN-2", resource_id=42)
    wire = CreateSerialNumbersResponse(successful=[sn1, sn2], failed=[])

    request = AddSerialNumbersRequest(
        resource_type="ManufacturingOrder",
        resource_id=42,
        serial_numbers=["MO-SN-1", "MO-SN-2"],
        preview=False,
    )

    with (
        patch(f"{_SN_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers.unwrap_as",
            return_value=wire,
        ),
        patch(
            "katana_mcp.tools.foundation.serial_numbers._invalidate_parent_cache",
            new_callable=AsyncMock,
        ),
    ):
        mock_api.return_value = _wrap_response(wire)
        response = await _add_serial_numbers_impl(request, context)

    assert response.is_preview is False
    assert response.semantic == "mint"
    assert [r.id for r in response.created] == [1001, 1002]
    assert [r.serial_number for r in response.created] == ["MO-SN-1", "MO-SN-2"]
    assert response.failed == []
    # Coaching hint for the MO mint case
    assert any("fulfill_order" in n for n in response.next_actions)
    # User-facing verb matches the semantic: mint → "Minted"
    assert response.message.startswith("Minted ")
    assert any("minted" in n for n in response.next_actions)


@pytest.mark.asyncio
async def test_add_serial_numbers_transfer_to_sor_normalizes_undefined_quirk():
    """Transfer response quirks (transaction_id='undefined', resource_id=None) surface as-is."""
    context, _ = create_mock_context()
    # Mimic the Katana wire quirk on transfer: transaction_id="undefined", resource_id=None
    transferred = _make_serial_number(
        id=886856,
        serial_number="HSC02647",
        resource_type=SerialNumberResourceType.SALESORDERROW,
        resource_id=None,
        transaction_id="undefined",
    )
    wire = CreateSerialNumbersResponse(successful=[transferred], failed=[])

    request = AddSerialNumbersRequest(
        resource_type="SalesOrderRow",
        resource_id=110029067,
        serial_numbers=["HSC02647"],
        preview=False,
    )

    with (
        patch(f"{_SN_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers.unwrap_as",
            return_value=wire,
        ),
        patch(
            "katana_mcp.tools.foundation.serial_numbers._invalidate_parent_cache",
            new_callable=AsyncMock,
        ),
    ):
        mock_api.return_value = _wrap_response(wire)
        response = await _add_serial_numbers_impl(request, context)

    assert response.semantic == "transfer"
    assert len(response.created) == 1
    record = response.created[0]
    assert record.id == 886856
    assert record.serial_number == "HSC02647"
    # The wire quirks are preserved (tool doesn't pretend they don't exist).
    assert record.transaction_id == "undefined"
    assert record.resource_id is None
    # User-facing verb matches the semantic: transfer → "Transferred"
    assert response.message.startswith("Transferred ")
    assert any("transferred" in n for n in response.next_actions)


# ============================================================================
# add_serial_numbers — partial failure / all-failed
# ============================================================================


@pytest.mark.asyncio
async def test_add_serial_numbers_partial_failure_duplicate():
    """DUPLICATE response: tool surfaces both successful and failed lists."""
    context, _ = create_mock_context()
    sn_ok = _make_serial_number(id=2001, serial_number="OK-1")
    failed = CreateSerialNumberFailedItem(
        serial_number="DUP-1",
        reason=CreateSerialNumberFailureReason.DUPLICATE,
    )
    wire = CreateSerialNumbersResponse(successful=[sn_ok], failed=[failed])

    request = AddSerialNumbersRequest(
        resource_type="ManufacturingOrder",
        resource_id=42,
        serial_numbers=["OK-1", "DUP-1"],
        preview=False,
    )

    with (
        patch(f"{_SN_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers.unwrap_as",
            return_value=wire,
        ),
        patch(
            "katana_mcp.tools.foundation.serial_numbers._invalidate_parent_cache",
            new_callable=AsyncMock,
        ),
    ):
        mock_api.return_value = _wrap_response(wire)
        response = await _add_serial_numbers_impl(request, context)

    assert [r.serial_number for r in response.created] == ["OK-1"]
    assert len(response.failed) == 1
    assert response.failed[0].reason == "DUPLICATE"
    assert response.failed[0].serial_number == "DUP-1"
    assert "Partial success" in response.message


@pytest.mark.asyncio
async def test_add_serial_numbers_all_missing_transfer():
    """Transfer attempt where every string is MISSING — no exception, surface failures."""
    context, _ = create_mock_context()
    failed = [
        CreateSerialNumberFailedItem(
            serial_number="GHOST-1",
            reason=CreateSerialNumberFailureReason.MISSING,
        )
    ]
    wire = CreateSerialNumbersResponse(successful=[], failed=failed)

    request = AddSerialNumbersRequest(
        resource_type="SalesOrderRow",
        resource_id=99,
        serial_numbers=["GHOST-1"],
        preview=False,
    )

    with (
        patch(f"{_SN_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers.unwrap_as",
            return_value=wire,
        ),
        patch(
            "katana_mcp.tools.foundation.serial_numbers._invalidate_parent_cache",
            new_callable=AsyncMock,
        ),
    ):
        mock_api.return_value = _wrap_response(wire)
        response = await _add_serial_numbers_impl(request, context)

    assert response.created == []
    assert response.failed[0].reason == "MISSING"
    # Transfer-path message uses "transferred", not "created".
    assert "No serial numbers transferred" in response.message
    assert "transfer path" in response.message


# ============================================================================
# add_serial_numbers — validation surface
# ============================================================================


def test_add_serial_numbers_accepts_production_as_transfer_type():
    """``Production`` is a valid write ``resource_type`` (transfer semantics) —
    verified live 2026-07-14 (#980): the wire routes it to a production lookup
    and 422s ``UnknownSerialNumber`` for a string that doesn't pre-exist."""
    from katana_mcp.tools.foundation.serial_numbers import _semantic_label

    request = AddSerialNumbersRequest(
        resource_type="Production",
        resource_id=1,
        serial_numbers=["X"],
        preview=False,
    )
    assert request.resource_type == "Production"
    assert _semantic_label("Production") == "transfer"


@pytest.mark.asyncio
async def test_add_serial_numbers_rejects_unknown_resource_type():
    """Pydantic Literal rejects a ``resource_type`` outside the write enum."""
    from pydantic import ValidationError

    # Cast the bad value to Any so the static checker doesn't refuse it
    # at type-check time — the test asserts pydantic catches it at runtime.
    bad_resource_type = cast(Any, "NotARealResourceType")
    with pytest.raises(ValidationError):
        AddSerialNumbersRequest(
            resource_type=bad_resource_type,
            resource_id=1,
            serial_numbers=["X"],
            preview=False,
        )


@pytest.mark.asyncio
async def test_add_serial_numbers_rejects_empty_list():
    """Pydantic min_length=1 rejects an empty serial_numbers list."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        AddSerialNumbersRequest(
            resource_type="ManufacturingOrder",
            resource_id=1,
            serial_numbers=[],
            preview=False,
        )


# ============================================================================
# add_serial_numbers — cross-resource parametrize (mint vs. transfer semantic)
# ============================================================================


@pytest.mark.parametrize(
    ("resource_type", "expected_semantic"),
    [
        ("ManufacturingOrder", "mint"),
        ("PurchaseOrderRow", "mint"),
        ("SalesOrderRow", "transfer"),
        ("StockTransferRow", "transfer"),
        ("StockAdjustmentRow", "transfer"),
    ],
)
@pytest.mark.asyncio
async def test_add_serial_numbers_semantic_classification(
    resource_type: str, expected_semantic: str
) -> None:
    """Each write resource_type maps to the correct mint/transfer bucket."""
    context, _ = create_mock_context()
    # Parametrize passes ``str``; pydantic validates the Literal at runtime.
    # Cast to Any so the static checker doesn't reject the wider input type.
    request = AddSerialNumbersRequest(
        resource_type=cast(Any, resource_type),
        resource_id=1,
        serial_numbers=["X"],
        preview=True,
    )
    response = await _add_serial_numbers_impl(request, context)
    assert response.semantic == expected_semantic


# ============================================================================
# list_serial_numbers
# ============================================================================


@pytest.mark.asyncio
async def test_list_serial_numbers_scoped():
    """Scoped list: resource_type + resource_id filters land on the request."""
    context, _ = create_mock_context()
    sn = _make_serial_number(id=5001, serial_number="LIST-1", resource_id=42)
    wire = SerialNumberListResponse(data=[sn])

    request = ListSerialNumbersRequest(
        resource_type="ManufacturingOrder",
        resource_id=42,
        limit=50,
        page=1,
    )

    with (
        patch(f"{_SN_LIST}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers.unwrap_as",
            return_value=wire,
        ),
    ):
        mock_api.return_value = _wrap_response(wire)
        response = await _list_serial_numbers_impl(request, context)

    assert len(response.serial_numbers) == 1
    assert response.serial_numbers[0].id == 5001
    assert response.page == 1
    assert response.limit == 50
    assert response.resource_type == "ManufacturingOrder"
    assert response.resource_id == 42

    # Confirm the API call carried the right filters
    call_kwargs = mock_api.call_args.kwargs
    assert call_kwargs["resource_id"] == 42
    assert call_kwargs["limit"] == 50
    assert call_kwargs["page"] == 1


@pytest.mark.asyncio
async def test_list_serial_numbers_empty_data():
    """data=[] (or UNSET) → empty list, no exception."""
    context, _ = create_mock_context()
    wire = SerialNumberListResponse(data=[])

    request = ListSerialNumbersRequest(limit=50, page=1)

    with (
        patch(f"{_SN_LIST}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers.unwrap_as",
            return_value=wire,
        ),
    ):
        mock_api.return_value = _wrap_response(wire)
        response = await _list_serial_numbers_impl(request, context)

    assert response.serial_numbers == []


@pytest.mark.asyncio
async def test_list_serial_numbers_page_beyond_data():
    """Page far beyond the dataset returns empty serial_numbers."""
    context, _ = create_mock_context()
    wire = SerialNumberListResponse(data=[])

    request = ListSerialNumbersRequest(page=99999, limit=50)

    with (
        patch(f"{_SN_LIST}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers.unwrap_as",
            return_value=wire,
        ),
    ):
        mock_api.return_value = _wrap_response(wire)
        response = await _list_serial_numbers_impl(request, context)

    assert response.serial_numbers == []
    assert response.page == 99999


@pytest.mark.asyncio
async def test_list_serial_numbers_no_filters():
    """Both filters absent: API kwargs use UNSET."""
    context, _ = create_mock_context()
    wire = SerialNumberListResponse(data=[])

    request = ListSerialNumbersRequest()

    with (
        patch(f"{_SN_LIST}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers.unwrap_as",
            return_value=wire,
        ),
    ):
        mock_api.return_value = _wrap_response(wire)
        await _list_serial_numbers_impl(request, context)

    call_kwargs = mock_api.call_args.kwargs
    assert call_kwargs["resource_type"] is UNSET
    assert call_kwargs["resource_id"] is UNSET


# ============================================================================
# delete_serial_numbers
# ============================================================================


@pytest.mark.asyncio
async def test_delete_serial_numbers_preview_does_not_call_api():
    """preview=True for delete returns the plan without calling Katana."""
    context, _ = create_mock_context()
    request = DeleteSerialNumbersRequest(
        resource_type="ManufacturingOrder",
        resource_id=42,
        ids=[1001, 1002],
        preview=True,
    )
    with patch(f"{_SN_DELETE}.asyncio_detailed", new_callable=AsyncMock) as mock_api:
        response = await _delete_serial_numbers_impl(request, context)

    mock_api.assert_not_called()
    assert response.is_preview is True
    assert response.deleted_ids == [1001, 1002]
    # The idempotency-caveat warning must surface on preview too.
    assert any("does not validate" in w for w in response.warnings)


@pytest.mark.asyncio
async def test_delete_serial_numbers_success_204():
    """DELETE returns 204 → tool echoes the requested ids."""
    context, _ = create_mock_context()
    request = DeleteSerialNumbersRequest(
        resource_type="ManufacturingOrder",
        resource_id=42,
        ids=[1001, 1002, 999999998],
        preview=False,
    )

    with (
        patch(f"{_SN_DELETE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers._invalidate_parent_cache",
            new_callable=AsyncMock,
        ),
    ):
        mock_api.return_value = _wrap_response(parsed=None, status=204)
        response = await _delete_serial_numbers_impl(request, context)

    assert response.is_preview is False
    # Echoes the request (Katana 204s without confirming).
    assert response.deleted_ids == [1001, 1002, 999999998]
    assert any("does not validate" in w for w in response.warnings)
    # Message says "Submitted", not "Deleted" — DELETE is unconditionally
    # idempotent, so we cannot truthfully claim per-id success.
    assert response.message.startswith("Submitted ")
    assert "Deleted" not in response.message


@pytest.mark.asyncio
async def test_delete_serial_numbers_idempotent():
    """Same id deleted twice → both calls return success, same echo."""
    context, _ = create_mock_context()
    request = DeleteSerialNumbersRequest(
        resource_type="ManufacturingOrder",
        resource_id=42,
        ids=[1001],
        preview=False,
    )

    with (
        patch(f"{_SN_DELETE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers._invalidate_parent_cache",
            new_callable=AsyncMock,
        ),
    ):
        mock_api.return_value = _wrap_response(parsed=None, status=204)
        first = await _delete_serial_numbers_impl(request, context)
        second = await _delete_serial_numbers_impl(request, context)

    assert first.deleted_ids == [1001]
    assert second.deleted_ids == [1001]


# ============================================================================
# Cache invalidation
# ============================================================================


@pytest.mark.asyncio
async def test_add_serial_numbers_invalidates_parent_mo_cache(
    context_with_typed_cache,
):
    """After a successful mint on an MO, the parent MO is evicted from cache."""
    from sqlmodel import select

    from katana_public_api_client.models_pydantic._generated import (
        CachedManufacturingOrder,
    )

    context, _, engine = context_with_typed_cache

    # Seed the cache with the parent MO so we can confirm it gets evicted.
    async with engine.session() as session:
        session.add(
            CachedManufacturingOrder(
                id=42,
                order_no="MO-42",
            )
        )
        await session.commit()

    sn = _make_serial_number(id=9001, serial_number="MO-X", resource_id=42)
    wire = CreateSerialNumbersResponse(successful=[sn], failed=[])

    request = AddSerialNumbersRequest(
        resource_type="ManufacturingOrder",
        resource_id=42,
        serial_numbers=["MO-X"],
        preview=False,
    )

    with (
        patch(f"{_SN_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers.unwrap_as",
            return_value=wire,
        ),
    ):
        mock_api.return_value = _wrap_response(wire)
        await _add_serial_numbers_impl(request, context)

    # The seeded MO row should be gone.
    async with engine.session() as session:
        result = await session.exec(
            select(CachedManufacturingOrder).where(CachedManufacturingOrder.id == 42)
        )
        assert result.one_or_none() is None


@pytest.mark.asyncio
async def test_delete_serial_numbers_invalidates_parent_mo_cache(
    context_with_typed_cache,
):
    """After a successful delete on an MO, the parent MO is evicted from cache."""
    from sqlmodel import select

    from katana_public_api_client.models_pydantic._generated import (
        CachedManufacturingOrder,
    )

    context, _, engine = context_with_typed_cache

    async with engine.session() as session:
        session.add(CachedManufacturingOrder(id=42, order_no="MO-42"))
        await session.commit()

    request = DeleteSerialNumbersRequest(
        resource_type="ManufacturingOrder",
        resource_id=42,
        ids=[1001],
        preview=False,
    )

    with patch(f"{_SN_DELETE}.asyncio_detailed", new_callable=AsyncMock) as mock_api:
        mock_api.return_value = _wrap_response(parsed=None, status=204)
        await _delete_serial_numbers_impl(request, context)

    async with engine.session() as session:
        result = await session.exec(
            select(CachedManufacturingOrder).where(CachedManufacturingOrder.id == 42)
        )
        assert result.one_or_none() is None


@pytest.mark.asyncio
async def test_add_serial_numbers_evicts_sor_row_not_parent_so(
    context_with_typed_cache,
):
    """SOR mint evicts the SOR row from cache, leaving the parent SO intact.

    The parent SalesOrder's ``updated_at`` doesn't advance on a row-level
    serial mutation, so deleting the parent would orphan it from the
    watermark sync. The row carries ``serial_numbers`` directly — evict
    the row to let the next read repopulate it.
    """
    from sqlmodel import select

    from katana_public_api_client.models_pydantic._generated import (
        CachedSalesOrder,
        CachedSalesOrderRow,
    )
    from tests.factories import make_sales_order, make_sales_order_row

    context, _, engine = context_with_typed_cache

    async with engine.session() as session:
        session.add(make_sales_order(id=100, order_no="SO-100"))
        session.add(make_sales_order_row(id=42, sales_order_id=100, variant_id=500))
        await session.commit()

    sn = _make_serial_number(id=9001, serial_number="SN-1", resource_id=42)
    wire = CreateSerialNumbersResponse(successful=[sn], failed=[])

    request = AddSerialNumbersRequest(
        resource_type="SalesOrderRow",
        resource_id=42,
        serial_numbers=["SN-1"],
        preview=False,
    )

    with (
        patch(f"{_SN_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers.unwrap_as",
            return_value=wire,
        ),
    ):
        mock_api.return_value = _wrap_response(wire)
        await _add_serial_numbers_impl(request, context)

    async with engine.session() as session:
        row_result = await session.exec(
            select(CachedSalesOrderRow).where(CachedSalesOrderRow.id == 42)
        )
        assert row_result.one_or_none() is None, (
            "SOR row should be evicted so the next read repopulates serial_numbers"
        )
        parent_result = await session.exec(
            select(CachedSalesOrder).where(CachedSalesOrder.id == 100)
        )
        assert parent_result.one_or_none() is not None, (
            "Parent SalesOrder must NOT be evicted — its updated_at doesn't "
            "advance on a row-level serial change, so deletion would orphan it."
        )


@pytest.mark.asyncio
async def test_add_serial_numbers_purchase_order_row_skips_cache_eviction(
    context_with_typed_cache,
):
    """PO row mint is a cache no-op — PO models don't surface serial_numbers."""
    from sqlmodel import select

    from katana_public_api_client.models_pydantic._generated import (
        CachedPurchaseOrder,
        CachedPurchaseOrderRow,
    )
    from tests.factories import make_purchase_order, make_purchase_order_row

    context, _, engine = context_with_typed_cache

    async with engine.session() as session:
        session.add(make_purchase_order(id=200, order_no="PO-200"))
        session.add(
            make_purchase_order_row(id=77, purchase_order_id=200, variant_id=501)
        )
        await session.commit()

    sn = _make_serial_number(id=9002, serial_number="PSN-1", resource_id=77)
    wire = CreateSerialNumbersResponse(successful=[sn], failed=[])

    request = AddSerialNumbersRequest(
        resource_type="PurchaseOrderRow",
        resource_id=77,
        serial_numbers=["PSN-1"],
        preview=False,
    )

    with (
        patch(f"{_SN_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers.unwrap_as",
            return_value=wire,
        ),
    ):
        mock_api.return_value = _wrap_response(wire)
        await _add_serial_numbers_impl(request, context)

    async with engine.session() as session:
        parent_result = await session.exec(
            select(CachedPurchaseOrder).where(CachedPurchaseOrder.id == 200)
        )
        assert parent_result.one_or_none() is not None
        row_result = await session.exec(
            select(CachedPurchaseOrderRow).where(CachedPurchaseOrderRow.id == 77)
        )
        assert row_result.one_or_none() is not None


# ============================================================================
# Tool registration / ToolResult shape
# ============================================================================


@pytest.mark.asyncio
async def test_register_tools_smoke():
    """register_tools installs three tools without raising."""
    mcp = MagicMock()
    mcp.tool = MagicMock(return_value=lambda fn: fn)
    register_tools(mcp)
    # Three tools (add, list, delete) — at least three @mcp.tool decorator calls.
    # ``register_preview_tool`` calls ``mcp.tool(...)`` so total tool() calls
    # is 3 regardless of preview/non-preview registration paths.
    assert mcp.tool.call_count >= 3


@pytest.mark.asyncio
async def test_list_serial_numbers_tool_result_content_is_json():
    """The MCP tool wrapper returns ToolResult whose content channel is JSON."""
    from katana_mcp.tools.foundation.serial_numbers import list_serial_numbers

    context, _ = create_mock_context()
    wire = SerialNumberListResponse(data=[])

    with (
        patch(f"{_SN_LIST}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools.foundation.serial_numbers.unwrap_as",
            return_value=wire,
        ),
    ):
        mock_api.return_value = _wrap_response(wire)
        result = await list_serial_numbers(
            resource_type=None,
            resource_id=None,
            limit=50,
            page=1,
            context=context,
        )

    # ToolResult.content is a list[TextContent] under FastMCP — convert to text
    # via .model_dump() or by reading .text.
    content_list = result.content
    assert content_list, "content channel should be populated"
    text = content_list[0].text
    parsed = json.loads(text)
    assert "serial_numbers" in parsed
    assert parsed["page"] == 1
