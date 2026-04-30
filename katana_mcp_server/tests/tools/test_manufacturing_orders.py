"""Tests for manufacturing order MCP tools."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.manufacturing_orders import (
    CreateManufacturingOrderRequest,
    DeleteManufacturingOrderRequest,
    GetManufacturingOrderRecipeRequest,
    ModifyManufacturingOrderRequest,
    MOHeaderPatch,
    MOOperationRowAdd,
    MOProductionAdd,
    MORecipeRowAdd,
    _create_manufacturing_order_impl,
    _delete_manufacturing_order_impl,
    _get_manufacturing_order_recipe_impl,
    _modify_manufacturing_order_impl,
    get_manufacturing_order,
    get_manufacturing_order_recipe,
    list_manufacturing_orders,
)

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    ManufacturingOrder,
    ManufacturingOrderStatus,
)
from katana_public_api_client.utils import APIError
from tests.conftest import create_mock_context, patch_typed_cache_sync
from tests.factories import (
    make_manufacturing_order,
    mock_entity_for_modify,
    seed_cache,
)

# ============================================================================
# Unit Tests (with mocks)
# ============================================================================


@pytest.mark.asyncio
async def test_create_manufacturing_order_preview():
    """Test create_manufacturing_order in preview mode."""
    context, _ = create_mock_context()

    request = CreateManufacturingOrderRequest(
        variant_id=2101,
        planned_quantity=50.0,
        location_id=1,
        production_deadline_date=datetime(2024, 1, 25, 17, 0, 0, tzinfo=UTC),
        additional_info="Priority order",
        confirm=False,
    )
    result = await _create_manufacturing_order_impl(request, context)

    assert result.is_preview is True
    assert result.variant_id == 2101
    assert result.planned_quantity == 50.0
    assert result.location_id == 1
    assert result.production_deadline_date == datetime(
        2024, 1, 25, 17, 0, 0, tzinfo=UTC
    )
    assert result.additional_info == "Priority order"
    assert result.id is None
    assert "preview" in result.message.lower()
    assert len(result.next_actions) > 0
    assert len(result.warnings) == 0  # All optional fields provided


@pytest.mark.asyncio
async def test_create_manufacturing_order_confirm_success():
    """Test create_manufacturing_order with confirm=True succeeds."""
    context, _lifespan_ctx = create_mock_context()

    # Mock successful API response
    mock_mo = ManufacturingOrder(
        id=3001,
        status=ManufacturingOrderStatus.NOT_STARTED,
        order_no="MO-2024-001",
        variant_id=2101,
        planned_quantity=50.0,
        location_id=1,
        order_created_date=datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC),
        production_deadline_date=datetime(2024, 1, 25, 17, 0, 0, tzinfo=UTC),
        additional_info="Priority order",
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_mo

    # Mock the API call
    mock_api_call = AsyncMock(return_value=mock_response)

    # Patch the API call
    import katana_public_api_client.api.manufacturing_order.create_manufacturing_order as create_mo_module

    original_asyncio_detailed = create_mo_module.asyncio_detailed
    create_mo_module.asyncio_detailed = mock_api_call

    try:
        request = CreateManufacturingOrderRequest(
            variant_id=2101,
            planned_quantity=50.0,
            location_id=1,
            production_deadline_date=datetime(2024, 1, 25, 17, 0, 0, tzinfo=UTC),
            additional_info="Priority order",
            confirm=True,
        )
        result = await _create_manufacturing_order_impl(request, context)

        assert result.is_preview is False
        assert result.id == 3001
        assert result.order_no == "MO-2024-001"
        assert result.variant_id == 2101
        assert result.planned_quantity == 50.0
        assert result.location_id == 1
        assert result.status == "NOT_STARTED"
        assert result.additional_info == "Priority order"
        assert "3001" in result.message
        assert len(result.next_actions) > 0

        # Verify API was called
        mock_api_call.assert_called_once()
    finally:
        # Restore original function
        create_mo_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_manufacturing_order_make_to_order_preview_populates_fields():
    """MTO preview must fetch the sales_order_row and populate variant_id /
    planned_quantity / location_id from it. Before this fix, these fields
    were left as None and the preview UI rendered empty.
    """
    from katana_public_api_client.models import SalesOrderRow

    context, _ = create_mock_context()

    # Sales order row that is NOT yet linked to an MO — happy path
    sor = SalesOrderRow(
        id=99001,
        quantity=7.0,
        variant_id=42424242,
        location_id=160000,
        sales_order_id=10000,
        linked_manufacturing_order_id=None,
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = sor

    import katana_public_api_client.api.sales_order_row.get_sales_order_row as get_sor_module

    original = get_sor_module.asyncio_detailed
    get_sor_module.asyncio_detailed = AsyncMock(return_value=mock_response)
    try:
        request = CreateManufacturingOrderRequest(
            sales_order_row_id=99001,
            confirm=False,
        )
        result = await _create_manufacturing_order_impl(request, context)

        assert result.is_preview is True
        # The whole point of the fix: these came from the fetched SO row,
        # not from request input (the request didn't provide them).
        assert result.variant_id == 42424242
        assert result.planned_quantity == 7.0
        assert result.location_id == 160000
        # No BLOCK warnings on the happy path → Confirm button stays.
        assert not any(w.startswith("BLOCK:") for w in result.warnings)
    finally:
        get_sor_module.asyncio_detailed = original


@pytest.mark.asyncio
async def test_create_manufacturing_order_make_to_order_confirm_refuses_when_already_linked():
    """confirm=True against a sales_order_row that's already linked to an MO
    must refuse — the preview UI's BLOCK warning suppresses the Confirm
    button in the iframe, but a programmatic caller skipping the UI gets
    the same defense-in-depth protection here.
    """
    from katana_public_api_client.models import SalesOrderRow

    context, _ = create_mock_context()

    sor = SalesOrderRow(
        id=99003,
        quantity=3.0,
        variant_id=42424244,
        location_id=160002,
        sales_order_id=10002,
        linked_manufacturing_order_id=77777,
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = sor

    # Also patch the MTO endpoint so we can assert it's NOT called.
    import katana_public_api_client.api.manufacturing_order.make_to_order_manufacturing_order as mto_module
    import katana_public_api_client.api.sales_order_row.get_sales_order_row as get_sor_module

    original_get = get_sor_module.asyncio_detailed
    original_mto = getattr(mto_module, "asyncio_detailed", None)
    get_sor_module.asyncio_detailed = AsyncMock(return_value=mock_response)
    mto_mock = AsyncMock()
    mto_module.asyncio_detailed = mto_mock
    try:
        request = CreateManufacturingOrderRequest(
            sales_order_row_id=99003,
            confirm=True,
        )
        result = await _create_manufacturing_order_impl(request, context)

        assert result.is_preview is False
        block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
        assert len(block_warnings) == 1
        assert "77777" in block_warnings[0]
        assert "Refused" in result.message
        # Critically: the MTO API must NOT have been called.
        mto_mock.assert_not_called()
    finally:
        get_sor_module.asyncio_detailed = original_get
        if original_mto is not None:
            mto_module.asyncio_detailed = original_mto


@pytest.mark.asyncio
async def test_create_manufacturing_order_make_to_order_blocks_when_already_linked():
    """When the sales_order_row already has a linked_manufacturing_order_id,
    the preview must emit a BLOCK warning so the UI builder suppresses the
    Confirm button — preventing duplicate MO creation.
    """
    from katana_public_api_client.models import SalesOrderRow

    context, _ = create_mock_context()

    sor = SalesOrderRow(
        id=99002,
        quantity=3.0,
        variant_id=42424243,
        location_id=160001,
        sales_order_id=10001,
        linked_manufacturing_order_id=88888,  # already linked!
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = sor

    import katana_public_api_client.api.sales_order_row.get_sales_order_row as get_sor_module

    original = get_sor_module.asyncio_detailed
    get_sor_module.asyncio_detailed = AsyncMock(return_value=mock_response)
    try:
        request = CreateManufacturingOrderRequest(
            sales_order_row_id=99002,
            confirm=False,
        )
        result = await _create_manufacturing_order_impl(request, context)

        assert result.is_preview is True
        # Fields still populated so the user sees the existing context.
        assert result.variant_id == 42424243
        # And the BLOCK warning is present.
        block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
        assert len(block_warnings) == 1
        assert "88888" in block_warnings[0]
        assert "already linked" in block_warnings[0]
    finally:
        get_sor_module.asyncio_detailed = original


@pytest.mark.asyncio
async def test_create_manufacturing_order_missing_optional_fields():
    """Test create_manufacturing_order handles missing optional fields."""
    context, _ = create_mock_context()

    request = CreateManufacturingOrderRequest(
        variant_id=2101,
        planned_quantity=50.0,
        location_id=1,
        confirm=False,
    )
    result = await _create_manufacturing_order_impl(request, context)

    assert result.is_preview is True
    assert result.variant_id == 2101
    assert result.planned_quantity == 50.0
    assert result.location_id == 1
    assert result.order_created_date is None
    assert result.production_deadline_date is None
    assert result.additional_info is None
    # Verify warnings for missing optional fields
    assert len(result.warnings) == 2
    assert any("production_deadline_date" in w for w in result.warnings)
    assert any("additional_info" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_create_manufacturing_order_confirm_with_minimal_fields():
    """Test create_manufacturing_order with only required fields."""
    context, _lifespan_ctx = create_mock_context()

    # Mock successful API response with minimal fields
    mock_mo = ManufacturingOrder(
        id=3002,
        status=ManufacturingOrderStatus.NOT_STARTED,
        order_no="MO-2024-002",
        variant_id=2102,
        planned_quantity=25.0,
        location_id=2,
        order_created_date=UNSET,
        production_deadline_date=UNSET,
        additional_info=UNSET,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_mo

    # Mock the API call
    mock_api_call = AsyncMock(return_value=mock_response)

    # Patch the API call
    import katana_public_api_client.api.manufacturing_order.create_manufacturing_order as create_mo_module

    original_asyncio_detailed = create_mo_module.asyncio_detailed
    create_mo_module.asyncio_detailed = mock_api_call

    try:
        request = CreateManufacturingOrderRequest(
            variant_id=2102,
            planned_quantity=25.0,
            location_id=2,
            confirm=True,
        )
        result = await _create_manufacturing_order_impl(request, context)

        assert result.is_preview is False
        assert result.id == 3002
        assert result.order_no == "MO-2024-002"
        assert result.variant_id == 2102
        assert result.planned_quantity == 25.0
        assert result.location_id == 2
        assert result.order_created_date is None
        assert result.production_deadline_date is None
        assert result.additional_info is None
    finally:
        # Restore original function
        create_mo_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_manufacturing_order_api_error():
    """Test create_manufacturing_order handles API errors."""
    context, _lifespan_ctx = create_mock_context()

    # Mock error response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.parsed = None

    mock_api_call = AsyncMock(return_value=mock_response)

    # Patch the API call
    import katana_public_api_client.api.manufacturing_order.create_manufacturing_order as create_mo_module

    original_asyncio_detailed = create_mo_module.asyncio_detailed
    create_mo_module.asyncio_detailed = mock_api_call

    try:
        request = CreateManufacturingOrderRequest(
            variant_id=2101,
            planned_quantity=50.0,
            location_id=1,
            confirm=True,
        )

        with pytest.raises(APIError):
            await _create_manufacturing_order_impl(request, context)
    finally:
        # Restore original function
        create_mo_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_manufacturing_order_api_exception():
    """Test create_manufacturing_order handles API exceptions."""
    context, _lifespan_ctx = create_mock_context()

    # Mock API call that raises exception
    mock_api_call = AsyncMock(side_effect=Exception("Network error"))

    # Patch the API call
    import katana_public_api_client.api.manufacturing_order.create_manufacturing_order as create_mo_module

    original_asyncio_detailed = create_mo_module.asyncio_detailed
    create_mo_module.asyncio_detailed = mock_api_call

    try:
        request = CreateManufacturingOrderRequest(
            variant_id=2101,
            planned_quantity=50.0,
            location_id=1,
            confirm=True,
        )

        with pytest.raises(Exception, match="Network error"):
            await _create_manufacturing_order_impl(request, context)
    finally:
        # Restore original function
        create_mo_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_manufacturing_order_with_order_created_date():
    """Test create_manufacturing_order with explicit order_created_date."""
    context, _ = create_mock_context()

    order_date = datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC)
    request = CreateManufacturingOrderRequest(
        variant_id=2101,
        planned_quantity=50.0,
        location_id=1,
        order_created_date=order_date,
        confirm=False,
    )
    result = await _create_manufacturing_order_impl(request, context)

    assert result.is_preview is True
    assert result.order_created_date == order_date


# ============================================================================
# Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_manufacturing_order_invalid_quantity():
    """Test create_manufacturing_order rejects invalid quantity."""
    # Pydantic will raise validation error for quantity <= 0
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateManufacturingOrderRequest(
            variant_id=2101,
            planned_quantity=0.0,  # Invalid: must be > 0
            location_id=1,
            confirm=False,
        )


@pytest.mark.asyncio
async def test_create_manufacturing_order_negative_quantity():
    """Test create_manufacturing_order rejects negative quantity."""
    # Pydantic will raise validation error for negative quantity
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateManufacturingOrderRequest(
            variant_id=2101,
            planned_quantity=-10.0,  # Invalid: must be > 0
            location_id=1,
            confirm=False,
        )


# ============================================================================
# Integration Tests (with real API)
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_manufacturing_order_preview_integration(katana_context):
    """Integration test: create_manufacturing_order preview with real Katana API.

    This test requires a valid KATANA_API_KEY in the environment.
    Tests preview mode which doesn't make API calls.
    """
    request = CreateManufacturingOrderRequest(
        variant_id=2101,
        planned_quantity=50.0,
        location_id=1,
        production_deadline_date=datetime(2024, 12, 31, 17, 0, 0, tzinfo=UTC),
        additional_info="Integration test preview",
        confirm=False,
    )

    try:
        result = await _create_manufacturing_order_impl(request, katana_context)

        # Verify response structure
        assert result.is_preview is True
        assert result.variant_id == 2101
        assert result.planned_quantity == 50.0
        assert result.location_id == 1
        assert isinstance(result.message, str)
        assert isinstance(result.next_actions, list)
        assert result.id is None  # Preview mode doesn't create
    except Exception as e:
        # Should not fail in preview mode
        pytest.fail(f"Preview mode should not fail: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_manufacturing_order_confirm_integration(katana_context):
    """Integration test: create_manufacturing_order confirm with real Katana API.

    This test requires a valid KATANA_API_KEY in the environment.
    Tests actual creation of manufacturing order.

    Note: This test may fail if:
    - API key is invalid
    - Network is unavailable
    - Variant doesn't exist
    - Location doesn't exist
    """
    request = CreateManufacturingOrderRequest(
        variant_id=2101,
        planned_quantity=1.0,  # Small quantity for test
        location_id=1,
        production_deadline_date=datetime(2024, 12, 31, 17, 0, 0, tzinfo=UTC),
        additional_info="Integration test - can be deleted",
        confirm=True,
    )

    try:
        result = await _create_manufacturing_order_impl(request, katana_context)

        # Verify response structure
        assert result.is_preview is False
        assert isinstance(result.id, int)
        assert result.id > 0
        assert isinstance(result.order_no, str) or result.order_no is None
        assert result.variant_id == 2101
        assert result.planned_quantity == 1.0
        assert result.location_id == 1
        assert isinstance(result.status, str) or result.status is None
        assert isinstance(result.message, str)
        assert len(result.next_actions) > 0

    except Exception as e:
        # Network/auth/validation errors are acceptable in integration tests
        error_msg = str(e).lower()
        assert any(
            word in error_msg
            for word in [
                "connection",
                "network",
                "auth",
                "timeout",
                "not found",
                "variant",
                "location",
                "invalid",
            ]
        ), f"Unexpected error: {e}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_manufacturing_order_minimal_fields_integration(katana_context):
    """Integration test: create_manufacturing_order with minimal fields.

    Tests creation with only required fields.
    """
    request = CreateManufacturingOrderRequest(
        variant_id=2101,
        planned_quantity=1.0,
        location_id=1,
        confirm=True,
    )

    try:
        result = await _create_manufacturing_order_impl(request, katana_context)

        # Verify response structure
        assert result.is_preview is False
        assert isinstance(result.id, int)
        assert result.variant_id == 2101
        assert result.planned_quantity == 1.0
        assert result.location_id == 1

    except Exception as e:
        # Network/auth/validation errors are acceptable in integration tests
        error_msg = str(e).lower()
        assert any(
            word in error_msg
            for word in [
                "connection",
                "network",
                "auth",
                "timeout",
                "not found",
                "variant",
                "location",
            ]
        ), f"Unexpected error: {e}"


# ============================================================================
# Recipe row tools — get, add, delete
# ============================================================================

_RECIPE_API = "katana_public_api_client.api.manufacturing_order_recipe"
_UNWRAP_DATA = "katana_public_api_client.utils.unwrap_data"


@pytest.mark.asyncio
async def test_get_manufacturing_order_recipe():
    """Test listing recipe rows for an MO."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_many_by_ids = AsyncMock(
        return_value={
            101: {"id": 101, "sku": "FORK-001"},
            102: {"id": 102, "sku": "BOLT-004"},
        }
    )

    def _mk_row(row_id: int, variant_id: int, qpu: float, cost: float) -> MagicMock:
        # _recipe_row_info_from_attrs now reads every ManufacturingOrderRecipeRow
        # field — explicitly set the ones it touches to UNSET or safe values so
        # MagicMock's auto-attributes don't leak into Pydantic validation.
        m = MagicMock()
        m.id = row_id
        m.variant_id = variant_id
        m.planned_quantity_per_unit = qpu
        m.total_actual_quantity = 0.0
        m.ingredient_availability = "IN_STOCK"
        m.notes = None
        m.cost = cost
        m.manufacturing_order_id = UNSET
        m.total_consumed_quantity = UNSET
        m.total_remaining_quantity = UNSET
        m.ingredient_expected_date = UNSET
        m.batch_transactions = UNSET
        m.created_at = UNSET
        m.updated_at = UNSET
        m.deleted_at = UNSET
        return m

    mock_row1 = _mk_row(5001, 101, 1.0, 250.0)
    mock_row2 = _mk_row(5002, 102, 4.0, 2.0)

    with (
        patch(
            f"{_RECIPE_API}.get_all_manufacturing_order_recipe_rows.asyncio_detailed",
            new_callable=AsyncMock,
        ),
        patch(_UNWRAP_DATA, return_value=[mock_row1, mock_row2]),
    ):
        request = GetManufacturingOrderRecipeRequest(manufacturing_order_id=9999)
        result = await _get_manufacturing_order_recipe_impl(request, context)

    assert result.total_count == 2
    assert result.rows[0].id == 5001
    assert result.rows[0].sku == "FORK-001"
    assert result.rows[1].sku == "BOLT-004"


@pytest.mark.asyncio
async def test_get_manufacturing_order_recipe_empty():
    """Test listing recipe rows when MO has no ingredients."""
    context, _ = create_mock_context()

    with (
        patch(
            f"{_RECIPE_API}.get_all_manufacturing_order_recipe_rows.asyncio_detailed",
            new_callable=AsyncMock,
        ),
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        request = GetManufacturingOrderRecipeRequest(manufacturing_order_id=9999)
        result = await _get_manufacturing_order_recipe_impl(request, context)

    assert result.total_count == 0
    assert result.rows == []


@pytest.mark.asyncio
async def test_create_manufacturing_order_make_to_order_preview():
    """Make-to-order preview mode: sales_order_row_id only, no other fields required."""
    from katana_public_api_client.models import SalesOrderRow

    context, _ = create_mock_context()

    sor = SalesOrderRow(
        id=105664660, quantity=2.0, variant_id=2101, location_id=1, sales_order_id=99
    )
    mock_response = MagicMock(status_code=200, parsed=sor)

    import katana_public_api_client.api.sales_order_row.get_sales_order_row as get_sor_module

    original = get_sor_module.asyncio_detailed
    get_sor_module.asyncio_detailed = AsyncMock(return_value=mock_response)
    try:
        request = CreateManufacturingOrderRequest(
            sales_order_row_id=105664660,
            confirm=False,
        )
        result = await _create_manufacturing_order_impl(request, context)

        assert result.is_preview is True
        assert "Make-to-order" in result.message or "make-to-order" in result.message
        assert "105664660" in result.message
    finally:
        get_sor_module.asyncio_detailed = original


@pytest.mark.asyncio
async def test_create_manufacturing_order_standalone_requires_fields():
    """Standalone mode without required fields raises ValueError."""
    context, _ = create_mock_context()

    request = CreateManufacturingOrderRequest(confirm=False)
    with pytest.raises(ValueError, match="variant_id"):
        await _create_manufacturing_order_impl(request, context)


@pytest.mark.asyncio
async def test_create_manufacturing_order_make_to_order_with_subassemblies():
    """Make-to-order with create_subassemblies=true."""
    from katana_public_api_client.models import SalesOrderRow

    context, _ = create_mock_context()

    sor = SalesOrderRow(
        id=105664660, quantity=2.0, variant_id=2101, location_id=1, sales_order_id=99
    )
    mock_response = MagicMock(status_code=200, parsed=sor)

    import katana_public_api_client.api.sales_order_row.get_sales_order_row as get_sor_module

    original = get_sor_module.asyncio_detailed
    get_sor_module.asyncio_detailed = AsyncMock(return_value=mock_response)
    try:
        request = CreateManufacturingOrderRequest(
            sales_order_row_id=105664660,
            create_subassemblies=True,
            confirm=False,
        )
        result = await _create_manufacturing_order_impl(request, context)

        assert result.is_preview is True
        assert "subassemblies" in result.message
    finally:
        get_sor_module.asyncio_detailed = original


# ============================================================================
# list_manufacturing_orders — cache-backed (#377)
# ============================================================================
#
# Tests seed ``CachedManufacturingOrder`` rows directly with ``make_manufacturing_order``
# and assert the impl's filter/pagination logic against the query results.
# The ``no_sync`` fixture stubs ``ensure_manufacturing_orders_synced`` so the
# impl never tries to talk to the API during these unit tests.


@pytest.fixture
def no_sync():
    """Patch ``ensure_manufacturing_orders_synced`` to a no-op."""
    with patch_typed_cache_sync("manufacturing_orders"):
        yield


@pytest.mark.asyncio
async def test_list_manufacturing_orders_limit_le_250_validation():
    """limit > 250 is rejected at the schema boundary."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
    )
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ListManufacturingOrdersRequest(limit=500)


@pytest.mark.asyncio
async def test_list_manufacturing_orders_filters_by_ids(
    context_with_typed_cache, no_sync
):
    """`ids` restricts the returned set to the specified MO IDs."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_manufacturing_order(id=1, order_no="MO-1"),
            make_manufacturing_order(id=2, order_no="MO-2"),
            make_manufacturing_order(id=3, order_no="MO-3"),
        ],
    )

    result = await _list_manufacturing_orders_impl(
        ListManufacturingOrdersRequest(ids=[1, 3]), context
    )

    assert {o.id for o in result.orders} == {1, 3}


@pytest.mark.asyncio
async def test_list_manufacturing_orders_filters_by_status(
    context_with_typed_cache, no_sync
):
    """`status` matches the cache's enum column exactly."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    from katana_public_api_client.models import GetAllManufacturingOrdersStatus

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_manufacturing_order(id=1, status="IN_PROGRESS"),
            make_manufacturing_order(id=2, status="NOT_STARTED"),
            make_manufacturing_order(id=3, status="DONE"),
        ],
    )

    result = await _list_manufacturing_orders_impl(
        ListManufacturingOrdersRequest(
            status=GetAllManufacturingOrdersStatus.IN_PROGRESS
        ),
        context,
    )

    assert {o.id for o in result.orders} == {1}


@pytest.mark.asyncio
async def test_list_manufacturing_orders_filters_by_location_and_so_link(
    context_with_typed_cache, no_sync
):
    """`location_id` and `is_linked_to_sales_order` apply as direct column filters."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_manufacturing_order(
                id=1, location_id=7, is_linked_to_sales_order=True, sales_order_id=100
            ),
            make_manufacturing_order(
                id=2, location_id=7, is_linked_to_sales_order=False
            ),
            make_manufacturing_order(
                id=3, location_id=8, is_linked_to_sales_order=True, sales_order_id=101
            ),
        ],
    )

    by_loc = await _list_manufacturing_orders_impl(
        ListManufacturingOrdersRequest(location_id=7), context
    )
    assert {o.id for o in by_loc.orders} == {1, 2}

    linked = await _list_manufacturing_orders_impl(
        ListManufacturingOrdersRequest(is_linked_to_sales_order=True), context
    )
    assert {o.id for o in linked.orders} == {1, 3}


@pytest.mark.asyncio
async def test_list_manufacturing_orders_excludes_deleted_by_default(
    context_with_typed_cache, no_sync
):
    """Soft-deleted MOs are filtered unless include_deleted=True."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_manufacturing_order(id=1, deleted_at=None),
            make_manufacturing_order(id=2, deleted_at=datetime(2026, 3, 15)),
        ],
    )

    default = await _list_manufacturing_orders_impl(
        ListManufacturingOrdersRequest(), context
    )
    assert {o.id for o in default.orders} == {1}

    with_deleted = await _list_manufacturing_orders_impl(
        ListManufacturingOrdersRequest(include_deleted=True), context
    )
    assert {o.id for o in with_deleted.orders} == {1, 2}


@pytest.mark.asyncio
async def test_list_manufacturing_orders_date_filters(
    context_with_typed_cache, no_sync
):
    """All four date columns (created_at, updated_at, production_deadline_date) apply as ranges."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_manufacturing_order(
                id=1,
                created_at=datetime(2026, 2, 15),
                production_deadline_date=datetime(2026, 4, 15),
            ),
            make_manufacturing_order(
                id=2,
                created_at=datetime(2026, 5, 1),
                production_deadline_date=datetime(2027, 1, 1),
            ),
        ],
    )

    # Created window
    created = await _list_manufacturing_orders_impl(
        ListManufacturingOrdersRequest(
            created_after="2026-01-01T00:00:00Z",
            created_before="2026-04-01T00:00:00Z",
        ),
        context,
    )
    assert {o.id for o in created.orders} == {1}

    # production_deadline window — was a client-side filter pre-cache,
    # now indexed SQL.
    deadline = await _list_manufacturing_orders_impl(
        ListManufacturingOrdersRequest(
            production_deadline_after="2026-04-01T00:00:00Z",
            production_deadline_before="2026-04-30T00:00:00Z",
        ),
        context,
    )
    assert {o.id for o in deadline.orders} == {1}


@pytest.mark.asyncio
async def test_list_manufacturing_orders_invalid_date_raises(
    context_with_typed_cache, no_sync
):
    """Malformed ISO-8601 for a date filter surfaces as ValueError."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _, _typed_cache = context_with_typed_cache

    with pytest.raises(ValueError, match=r"Invalid ISO-8601.*created_after"):
        await _list_manufacturing_orders_impl(
            ListManufacturingOrdersRequest(created_after="not-a-date"), context
        )


@pytest.mark.asyncio
async def test_list_manufacturing_orders_caps_to_limit(
    context_with_typed_cache, no_sync
):
    """`limit` caps the result size even when more rows match."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [make_manufacturing_order(id=i) for i in range(1, 31)],
    )

    result = await _list_manufacturing_orders_impl(
        ListManufacturingOrdersRequest(limit=5), context
    )

    assert len(result.orders) == 5
    assert result.total_count == 5


@pytest.mark.asyncio
async def test_list_manufacturing_orders_pagination_meta_populated_on_explicit_page(
    context_with_typed_cache, no_sync
):
    """An explicit `page` populates `pagination` from a SQL COUNT against the same filter set."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [make_manufacturing_order(id=i) for i in range(1, 12)],
    )

    result = await _list_manufacturing_orders_impl(
        ListManufacturingOrdersRequest(limit=5, page=2), context
    )

    assert result.pagination is not None
    assert result.pagination.total_records == 11
    assert result.pagination.total_pages == 3
    assert result.pagination.page == 2
    assert result.pagination.first_page is False
    assert result.pagination.last_page is False
    assert len(result.orders) == 5


@pytest.mark.asyncio
async def test_list_manufacturing_orders_pagination_meta_none_without_page(
    context_with_typed_cache, no_sync
):
    """Without an explicit `page`, `pagination` is `None`."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(typed_cache, [make_manufacturing_order(id=1)])

    result = await _list_manufacturing_orders_impl(
        ListManufacturingOrdersRequest(limit=50), context
    )

    assert result.pagination is None


# ============================================================================
# format=json (manufacturing_orders tools)
# ============================================================================


def _content_text(result) -> str:
    return result.content[0].text


@pytest.mark.asyncio
async def test_list_manufacturing_orders_format_json_returns_json():
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._list_manufacturing_orders_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = ListManufacturingOrdersResponse(
            orders=[], total_count=0, pagination=None
        )
        result = await list_manufacturing_orders(format="json", context=context)

    data = json.loads(_content_text(result))
    assert data["total_count"] == 0


@pytest.mark.asyncio
async def test_get_manufacturing_order_format_json_returns_json():
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = GetManufacturingOrderResponse(
            id=3001,
            order_no="MO-2024-001",
            status="IN_PROGRESS",
        )
        result = await get_manufacturing_order(
            order_id=1, format="json", context=context
        )

    data = json.loads(_content_text(result))
    assert data["id"] == 3001
    assert data["order_no"] == "MO-2024-001"
    assert data["status"] == "IN_PROGRESS"
    # Default include_rows="blocking" returns an empty list (zero blocking
    # rows on this stub); operation_rows + productions are off by default,
    # so they're omitted entirely from the JSON.
    assert data["recipe_rows"] == []
    assert "operation_rows" not in data
    assert "productions" not in data


@pytest.mark.asyncio
async def test_get_manufacturing_order_recipe_format_json_returns_json():
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderRecipeResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_recipe_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = GetManufacturingOrderRecipeResponse(
            manufacturing_order_id=7, rows=[], total_count=0
        )
        result = await get_manufacturing_order_recipe(
            manufacturing_order_id=7, format="json", context=context
        )

    data = json.loads(_content_text(result))
    assert data["manufacturing_order_id"] == 7
    assert data["total_count"] == 0


# ============================================================================
# Exhaustive get_manufacturing_order (#346)
# ============================================================================

_FETCH_RECIPE = "katana_mcp.tools.foundation.manufacturing_orders._fetch_mo_recipe_rows"
_FETCH_OPS = "katana_mcp.tools.foundation.manufacturing_orders._fetch_mo_operation_rows"
_FETCH_PRODS = "katana_mcp.tools.foundation.manufacturing_orders._fetch_mo_productions"
_MO_API = "katana_public_api_client.api.manufacturing_order"


def _full_mo_attrs():
    """Build a ManufacturingOrder attrs model with every field populated.

    Used by the exhaustive-coverage tests to prove ``GetManufacturingOrderResponse``
    surfaces every field on the generated attrs model.
    """
    from katana_public_api_client.models import (
        ManufacturingOrder,
        ManufacturingOrderStatus,
    )
    from katana_public_api_client.models.ingredient_availability import (
        IngredientAvailability,
    )

    return ManufacturingOrder(
        id=3001,
        created_at=datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 20, 14, 30, 0, tzinfo=UTC),
        deleted_at=None,
        status=ManufacturingOrderStatus.IN_PROGRESS,
        order_no="MO-2024-001",
        variant_id=2101,
        planned_quantity=50.0,
        actual_quantity=35.0,
        completed_quantity=30.0,
        remaining_quantity=20.0,
        includes_partial_completions=True,
        batch_transactions=[],
        location_id=1,
        order_created_date=datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC),
        production_deadline_date=datetime(2024, 1, 25, 17, 0, 0, tzinfo=UTC),
        done_date=None,
        additional_info="Priority order",
        is_linked_to_sales_order=True,
        ingredient_availability=IngredientAvailability.IN_STOCK,
        total_cost=12500.0,
        total_actual_time=140.5,
        total_planned_time=200.0,
        sales_order_id=2001,
        sales_order_row_id=2501,
        sales_order_delivery_deadline=datetime(2024, 1, 30, 12, 0, 0, tzinfo=UTC),
        material_cost=8750.0,
        subassemblies_cost=2250.0,
        operations_cost=1500.0,
        serial_numbers=[],
    )


@pytest.mark.asyncio
async def test_get_manufacturing_order_full_field_coverage():
    """Every attrs-model field on ManufacturingOrder must flow to the response.

    Pins the #346 exhaustive-coverage contract: previous versions of
    GetManufacturingOrderResponse dropped 13 fields (created_at, updated_at,
    deleted_at, completed_quantity, remaining_quantity, includes_partial_completions,
    batch_transactions, total_actual_time, total_planned_time, sales_order_row_id,
    sales_order_delivery_deadline, subassemblies_cost, serial_numbers). All must
    round-trip through _build_mo_response.
    """
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderRequest,
        _get_manufacturing_order_impl,
    )

    context, _ = create_mock_context()
    mo = _full_mo_attrs()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mo

    with (
        patch(
            f"{_MO_API}.get_manufacturing_order.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=mock_response,
        ),
        patch(_FETCH_RECIPE, new_callable=AsyncMock, return_value=[]),
        patch(_FETCH_OPS, new_callable=AsyncMock, return_value=[]),
        patch(_FETCH_PRODS, new_callable=AsyncMock, return_value=[]),
    ):
        # Legacy shape: opt back into every collection to preserve the
        # exhaustive-field contract this test pins.
        request = GetManufacturingOrderRequest(
            order_id=3001,
            include_rows="all",
            include_operation_rows=True,
            include_productions=True,
            verbose=True,
        )
        result = await _get_manufacturing_order_impl(request, context)

    # Every scalar field on ManufacturingOrder must reach the response:
    assert result.id == 3001
    assert result.order_no == "MO-2024-001"
    assert result.status == "IN_PROGRESS"
    assert result.variant_id == 2101
    assert result.planned_quantity == 50.0
    assert result.actual_quantity == 35.0
    # Previously-dropped fields:
    assert result.completed_quantity == 30.0
    assert result.remaining_quantity == 20.0
    assert result.includes_partial_completions is True
    assert result.total_actual_time == 140.5
    assert result.total_planned_time == 200.0
    assert result.sales_order_row_id == 2501
    assert result.sales_order_delivery_deadline == "2024-01-30T12:00:00+00:00"
    assert result.subassemblies_cost == 2250.0
    assert result.created_at == "2024-01-15T08:00:00+00:00"
    assert result.updated_at == "2024-01-20T14:30:00+00:00"
    assert result.deleted_at is None
    assert result.batch_transactions == []
    assert result.serial_numbers == []
    # Fields that were already there stay correct:
    assert result.location_id == 1
    assert result.additional_info == "Priority order"
    assert result.ingredient_availability == "IN_STOCK"
    assert result.total_cost == 12500.0
    assert result.material_cost == 8750.0
    assert result.operations_cost == 1500.0
    assert result.sales_order_id == 2001
    assert result.is_linked_to_sales_order is True


@pytest.mark.asyncio
async def test_get_manufacturing_order_fetches_related_resources():
    """Recipe rows, operation rows, and productions come from their own endpoints.

    Patches the three _fetch_mo_* helpers to assert that:
      (a) each is invoked exactly once with the MO id, and
      (b) their results flow through to the response's list-shaped fields.
    """
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderRequest,
        OperationRowInfo,
        ProductionInfo,
        RecipeRowInfo,
        _get_manufacturing_order_impl,
    )

    context, _ = create_mock_context()
    mo = _full_mo_attrs()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mo

    recipe_row = RecipeRowInfo(
        id=4001,
        manufacturing_order_id=3001,
        variant_id=3201,
        sku="STEEL-304",
        planned_quantity_per_unit=2.5,
        total_actual_quantity=125.0,
        ingredient_availability="IN_STOCK",
        notes="Use only grade 304 material",
        cost=437.5,
    )
    operation_row = OperationRowInfo(
        id=3801,
        manufacturing_order_id=3001,
        status="IN_PROGRESS",
        operation_name="Cut Steel Sheets",
        planned_time_per_unit=15.0,
        total_actual_time=12.5,
    )
    production = ProductionInfo(
        id=3501,
        manufacturing_order_id=3001,
        quantity=25.0,
        production_date="2024-01-20T14:30:00+00:00",
    )

    with (
        patch(
            f"{_MO_API}.get_manufacturing_order.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=mock_response,
        ),
        patch(
            _FETCH_RECIPE, new_callable=AsyncMock, return_value=[recipe_row]
        ) as mock_fetch_recipe,
        patch(
            _FETCH_OPS, new_callable=AsyncMock, return_value=[operation_row]
        ) as mock_fetch_ops,
        patch(
            _FETCH_PRODS, new_callable=AsyncMock, return_value=[production]
        ) as mock_fetch_prods,
    ):
        # Legacy shape: opt back into every collection so all three fetch
        # helpers are awaited and the recipe row (IN_STOCK) survives the
        # default "blocking" filter.
        request = GetManufacturingOrderRequest(
            order_id=3001,
            include_rows="all",
            include_operation_rows=True,
            include_productions=True,
        )
        result = await _get_manufacturing_order_impl(request, context)

    # Each helper called exactly once with the MO id:
    mock_fetch_recipe.assert_awaited_once()
    assert mock_fetch_recipe.await_args.args[1] == 3001
    mock_fetch_ops.assert_awaited_once()
    assert mock_fetch_ops.await_args.args[1] == 3001
    mock_fetch_prods.assert_awaited_once()
    assert mock_fetch_prods.await_args.args[1] == 3001

    # Results flow through to the response:
    assert len(result.recipe_rows) == 1
    assert result.recipe_rows[0].id == 4001
    assert result.recipe_rows[0].sku == "STEEL-304"
    assert len(result.operation_rows) == 1
    assert result.operation_rows[0].operation_name == "Cut Steel Sheets"
    assert len(result.productions) == 1
    assert result.productions[0].quantity == 25.0


@pytest.mark.asyncio
async def test_get_manufacturing_order_markdown_uses_canonical_field_names():
    """Markdown labels use Pydantic field names (not prettified headers) so
    LLM consumers can't misread a section label as a different field
    (motivation: #346 follow-on, supplier_item_codes misread)."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = GetManufacturingOrderResponse(
            id=3001,
            order_no="MO-2024-001",
            status="IN_PROGRESS",
            variant_id=2101,
            planned_quantity=50.0,
            production_deadline_date="2024-01-25T17:00:00+00:00",
            total_cost=12500.0,
            subassemblies_cost=2250.0,
            sales_order_row_id=2501,
        )
        # Verbose-mode rendering pins the explicit-empty-list contract.
        # Compact mode (the default) suppresses ``**field**: []`` placeholders
        # to keep the response small — that surface is exercised by separate
        # compact-mode tests below.
        result = await get_manufacturing_order(
            order_id=3001,
            include_rows="all",
            include_operation_rows=True,
            include_productions=True,
            verbose=True,
            context=context,
        )

    text = result.content[0].text
    # Canonical scalar labels — the prettified versions the old impl used
    # (e.g. "**Deadline**:", "**Total Cost**:") are gone. These pin the
    # new convention:
    assert "**production_deadline_date**: 2024-01-25T17:00:00+00:00" in text
    assert "**total_cost**: 12500.0" in text
    assert "**subassemblies_cost**: 2250.0" in text
    assert "**sales_order_row_id**: 2501" in text
    # Empty list fields render with explicit [] syntax, not bare headers
    # that a reader might mistake for a section:
    assert "**recipe_rows**: []" in text
    assert "**operation_rows**: []" in text
    assert "**productions**: []" in text
    assert "**batch_transactions**: []" in text
    assert "**serial_numbers**: []" in text


@pytest.mark.asyncio
async def test_get_manufacturing_order_recipe_full_field_coverage():
    """RecipeRowInfo must surface every field on ManufacturingOrderRecipeRow.

    The pre-#346 RecipeRowInfo dropped 8 fields (created_at, updated_at,
    deleted_at, manufacturing_order_id, ingredient_expected_date,
    batch_transactions, total_consumed_quantity, total_remaining_quantity).
    """
    from katana_mcp.tools.foundation.manufacturing_orders import (
        _recipe_row_info_from_attrs,
    )

    from katana_public_api_client.models.manufacturing_order_recipe_row import (
        ManufacturingOrderRecipeRow,
    )
    from katana_public_api_client.models.manufacturing_order_recipe_row_batch_transactions_item import (
        ManufacturingOrderRecipeRowBatchTransactionsItem,
    )

    attrs_row = ManufacturingOrderRecipeRow(
        id=4001,
        created_at=datetime(2024, 1, 15, 8, 0, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 20, 14, 30, 0, tzinfo=UTC),
        deleted_at=None,
        manufacturing_order_id=3001,
        variant_id=3201,
        notes="Use only grade 304 material",
        planned_quantity_per_unit=2.5,
        total_actual_quantity=125.0,
        ingredient_availability="IN_STOCK",
        ingredient_expected_date=datetime(2024, 1, 18, 0, 0, 0, tzinfo=UTC),
        batch_transactions=[
            ManufacturingOrderRecipeRowBatchTransactionsItem(
                batch_id=1201, quantity=125.0
            )
        ],
        cost=437.5,
        total_consumed_quantity=100.0,
        total_remaining_quantity=25.0,
    )

    info = _recipe_row_info_from_attrs(attrs_row, sku="STEEL-304")

    # Previously-dropped fields:
    assert info.manufacturing_order_id == 3001
    assert info.total_consumed_quantity == 100.0
    assert info.total_remaining_quantity == 25.0
    assert info.ingredient_expected_date == "2024-01-18T00:00:00+00:00"
    assert info.created_at == "2024-01-15T08:00:00+00:00"
    assert info.updated_at == "2024-01-20T14:30:00+00:00"
    assert info.deleted_at is None
    assert len(info.batch_transactions) == 1
    assert info.batch_transactions[0].batch_id == 1201
    assert info.batch_transactions[0].quantity == 125.0
    # Fields that were already there stay correct:
    assert info.id == 4001
    assert info.variant_id == 3201
    assert info.sku == "STEEL-304"
    assert info.notes == "Use only grade 304 material"
    assert info.planned_quantity_per_unit == 2.5
    assert info.total_actual_quantity == 125.0
    assert info.ingredient_availability == "IN_STOCK"
    assert info.cost == 437.5


# ============================================================================
# Compact-by-default get_manufacturing_order
# ============================================================================


def _mk_recipe_row(
    *,
    id: int,
    availability: str,
    variant_id: int = 200,
    sku: str | None = None,
):
    """Build a minimal RecipeRowInfo for compact-mode tests."""
    from katana_mcp.tools.foundation.manufacturing_orders import RecipeRowInfo

    return RecipeRowInfo(
        id=id,
        manufacturing_order_id=3001,
        variant_id=variant_id,
        sku=sku,
        ingredient_availability=availability,
        created_at="2024-01-15T08:00:00+00:00",
        updated_at="2024-01-20T14:30:00+00:00",
    )


@pytest.mark.asyncio
async def test_get_manufacturing_order_default_filters_to_blocking_rows():
    """Default include_rows='blocking' drops IN_STOCK and other non-blocking rows.

    Procurement triage view: a Mayhem-140 build has dozens of IN_STOCK rows,
    a few NOT_AVAILABLE/EXPECTED rows. Only the blocking ones survive.
    """
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderRequest,
        _get_manufacturing_order_impl,
    )

    context, _ = create_mock_context()
    mo = _full_mo_attrs()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mo

    rows = [
        _mk_recipe_row(id=1, availability="IN_STOCK"),
        _mk_recipe_row(id=2, availability="NOT_AVAILABLE"),
        _mk_recipe_row(id=3, availability="EXPECTED"),
        _mk_recipe_row(id=4, availability="PROCESSED"),
        _mk_recipe_row(id=5, availability="NOT_APPLICABLE"),
    ]

    with (
        patch(
            f"{_MO_API}.get_manufacturing_order.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=mock_response,
        ),
        patch(_FETCH_RECIPE, new_callable=AsyncMock, return_value=rows),
        patch(_FETCH_OPS, new_callable=AsyncMock, return_value=[]) as mock_ops,
        patch(_FETCH_PRODS, new_callable=AsyncMock, return_value=[]) as mock_prods,
    ):
        result = await _get_manufacturing_order_impl(
            GetManufacturingOrderRequest(order_id=3001), context
        )

    assert {r.id for r in result.recipe_rows} == {2, 3}
    # Operation rows / productions are off by default → no upstream calls.
    mock_ops.assert_not_awaited()
    mock_prods.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_manufacturing_order_include_rows_none_skips_recipe_fetch():
    """include_rows='none' skips the recipe fetch entirely."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderRequest,
        _get_manufacturing_order_impl,
    )

    context, _ = create_mock_context()
    mo = _full_mo_attrs()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mo

    with (
        patch(
            f"{_MO_API}.get_manufacturing_order.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=mock_response,
        ),
        patch(_FETCH_RECIPE, new_callable=AsyncMock) as mock_recipe,
        patch(_FETCH_OPS, new_callable=AsyncMock) as mock_ops,
        patch(_FETCH_PRODS, new_callable=AsyncMock) as mock_prods,
    ):
        result = await _get_manufacturing_order_impl(
            GetManufacturingOrderRequest(order_id=3001, include_rows="none"), context
        )

    mock_recipe.assert_not_awaited()
    mock_ops.assert_not_awaited()
    mock_prods.assert_not_awaited()
    assert result.recipe_rows == []
    assert result.operation_rows == []
    assert result.productions == []


@pytest.mark.asyncio
async def test_get_manufacturing_order_include_rows_all_keeps_in_stock():
    """include_rows='all' returns every recipe row regardless of availability."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderRequest,
        _get_manufacturing_order_impl,
    )

    context, _ = create_mock_context()
    mo = _full_mo_attrs()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mo

    rows = [
        _mk_recipe_row(id=1, availability="IN_STOCK"),
        _mk_recipe_row(id=2, availability="NOT_AVAILABLE"),
    ]

    with (
        patch(
            f"{_MO_API}.get_manufacturing_order.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=mock_response,
        ),
        patch(_FETCH_RECIPE, new_callable=AsyncMock, return_value=rows),
        patch(_FETCH_OPS, new_callable=AsyncMock, return_value=[]),
        patch(_FETCH_PRODS, new_callable=AsyncMock, return_value=[]),
    ):
        result = await _get_manufacturing_order_impl(
            GetManufacturingOrderRequest(order_id=3001, include_rows="all"),
            context,
        )

    assert {r.id for r in result.recipe_rows} == {1, 2}


@pytest.mark.asyncio
async def test_get_manufacturing_order_compact_json_strips_row_metadata():
    """Compact mode JSON drops created_at/updated_at/deleted_at on recipe rows."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = GetManufacturingOrderResponse(
            id=3001,
            order_no="MO-X",
            recipe_rows=[
                _mk_recipe_row(id=1, availability="NOT_AVAILABLE"),
            ],
        )
        result = await get_manufacturing_order(
            order_id=3001, format="json", context=context
        )

    data = json.loads(_content_text(result))
    row = data["recipe_rows"][0]
    assert "created_at" not in row
    assert "updated_at" not in row
    assert "deleted_at" not in row
    # Substantive fields survive:
    assert row["id"] == 1
    assert row["ingredient_availability"] == "NOT_AVAILABLE"


@pytest.mark.asyncio
async def test_get_manufacturing_order_verbose_json_keeps_row_metadata():
    """verbose=True restores the metadata fields on every row."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = GetManufacturingOrderResponse(
            id=3001,
            order_no="MO-X",
            recipe_rows=[
                _mk_recipe_row(id=1, availability="NOT_AVAILABLE"),
            ],
        )
        result = await get_manufacturing_order(
            order_id=3001, format="json", verbose=True, context=context
        )

    data = json.loads(_content_text(result))
    row = data["recipe_rows"][0]
    assert row["created_at"] == "2024-01-15T08:00:00+00:00"
    assert row["updated_at"] == "2024-01-20T14:30:00+00:00"


@pytest.mark.asyncio
async def test_get_manufacturing_order_compact_markdown_omits_empty_lists():
    """Compact markdown does not emit ``**field**: []`` placeholders for
    suppressed/empty collections."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = GetManufacturingOrderResponse(
            id=3001,
            order_no="MO-X",
            status="IN_PROGRESS",
        )
        result = await get_manufacturing_order(order_id=3001, context=context)

    text = result.content[0].text
    # No bracketed-empty placeholders in compact mode.
    assert "**recipe_rows**: []" not in text
    assert "**operation_rows**: []" not in text
    assert "**productions**: []" not in text
    assert "**batch_transactions**: []" not in text
    assert "**serial_numbers**: []" not in text
    # Suppressed collections do not appear at all (no canonical-name header,
    # no decorated label, no annotation note).
    assert "**recipe_rows**" not in text
    assert "**operation_rows**" not in text
    assert "**productions**" not in text
    assert "filtered to blocking rows only" not in text
    # Scalar header is still rendered.
    assert "**status**: IN_PROGRESS" in text


# ============================================================================
# list_manufacturing_orders ingredient_availability column
# ============================================================================


@pytest.mark.asyncio
async def test_list_manufacturing_orders_includes_ingredient_availability(
    context_with_typed_cache, no_sync
):
    """The list summary surfaces the rolled-up MO-level availability."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListManufacturingOrdersRequest,
        _list_manufacturing_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_manufacturing_order(
                id=1, order_no="MO-1", ingredient_availability="IN_STOCK"
            ),
            make_manufacturing_order(
                id=2, order_no="MO-2", ingredient_availability="NOT_AVAILABLE"
            ),
            make_manufacturing_order(
                id=3, order_no="MO-3", ingredient_availability=None
            ),
        ],
    )

    result = await _list_manufacturing_orders_impl(
        ListManufacturingOrdersRequest(), context
    )

    by_id = {o.id: o.ingredient_availability for o in result.orders}
    assert by_id == {1: "IN_STOCK", 2: "NOT_AVAILABLE", 3: None}


# ============================================================================
# list_blocking_ingredients
# ============================================================================


@pytest.fixture
def no_sync_recipe_rows():
    """Patch typed-cache sync for both MOs and recipe rows (used by the rollup)."""
    with (
        patch_typed_cache_sync("manufacturing_orders"),
        patch_typed_cache_sync("manufacturing_order_recipe_rows"),
    ):
        yield


def _stub_variant_cache(context, sku_by_id: dict[int, str]) -> None:
    """Stub services.cache.get_many_by_ids(VARIANT, ...) to return SKUs for tests."""

    async def _lookup(_entity_type, vids):
        return {vid: {"sku": sku_by_id[vid]} for vid in vids if vid in sku_by_id}

    context.request_context.lifespan_context.cache.get_many_by_ids = AsyncMock(
        side_effect=_lookup
    )


@pytest.mark.asyncio
async def test_list_blocking_ingredients_aggregates_by_variant(
    context_with_typed_cache, no_sync_recipe_rows
):
    """Three MOs blocked on the same variant → one rollup row, count=3."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListBlockingIngredientsRequest,
        _list_blocking_ingredients_impl,
    )

    from tests.factories import make_manufacturing_order_recipe_row

    context, _, typed_cache = context_with_typed_cache
    _stub_variant_cache(context, {500: "WHEEL-29"})

    await seed_cache(
        typed_cache,
        [
            make_manufacturing_order(id=1, order_no="MO-1", status="IN_PROGRESS"),
            make_manufacturing_order(id=2, order_no="MO-2", status="NOT_STARTED"),
            make_manufacturing_order(id=3, order_no="MO-3", status="IN_PROGRESS"),
            make_manufacturing_order_recipe_row(
                id=11,
                manufacturing_order_id=1,
                variant_id=500,
                planned_quantity_per_unit=2.0,
                total_remaining_quantity=4.0,
                ingredient_availability="NOT_AVAILABLE",
            ),
            make_manufacturing_order_recipe_row(
                id=12,
                manufacturing_order_id=2,
                variant_id=500,
                planned_quantity_per_unit=2.0,
                total_remaining_quantity=4.0,
                ingredient_availability="EXPECTED",
            ),
            make_manufacturing_order_recipe_row(
                id=13,
                manufacturing_order_id=3,
                variant_id=500,
                planned_quantity_per_unit=2.0,
                total_remaining_quantity=4.0,
                ingredient_availability="NOT_AVAILABLE",
            ),
        ],
    )

    result = await _list_blocking_ingredients_impl(
        ListBlockingIngredientsRequest(), context
    )

    assert result.total_blocking_rows == 3
    assert result.total_affected_mos == 3
    assert result.by_mo is None
    assert result.by_variant is not None and len(result.by_variant) == 1
    rollup = result.by_variant[0]
    assert rollup.variant_id == 500
    assert rollup.sku == "WHEEL-29"
    assert rollup.affected_mo_count == 3
    assert sorted(rollup.affected_mo_order_nos) == ["MO-1", "MO-2", "MO-3"]
    assert rollup.total_remaining_quantity == 12.0


@pytest.mark.asyncio
async def test_list_blocking_ingredients_excludes_in_stock_rows(
    context_with_typed_cache, no_sync_recipe_rows
):
    """IN_STOCK and other non-blocking rows must not enter the rollup."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListBlockingIngredientsRequest,
        _list_blocking_ingredients_impl,
    )

    from tests.factories import make_manufacturing_order_recipe_row

    context, _, typed_cache = context_with_typed_cache
    _stub_variant_cache(context, {500: "WHEEL", 600: "FORK"})

    await seed_cache(
        typed_cache,
        [
            make_manufacturing_order(id=1, order_no="MO-1", status="IN_PROGRESS"),
            make_manufacturing_order_recipe_row(
                id=11,
                manufacturing_order_id=1,
                variant_id=500,
                ingredient_availability="IN_STOCK",
            ),
            make_manufacturing_order_recipe_row(
                id=12,
                manufacturing_order_id=1,
                variant_id=600,
                ingredient_availability="NOT_AVAILABLE",
                total_remaining_quantity=2.0,
            ),
        ],
    )

    result = await _list_blocking_ingredients_impl(
        ListBlockingIngredientsRequest(), context
    )

    assert result.total_blocking_rows == 1
    assert result.by_variant is not None and len(result.by_variant) == 1
    assert result.by_variant[0].variant_id == 600


@pytest.mark.asyncio
async def test_list_blocking_ingredients_filters_by_status(
    context_with_typed_cache, no_sync_recipe_rows
):
    """Default scope is NOT_STARTED + IN_PROGRESS — DONE MOs are excluded."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListBlockingIngredientsRequest,
        _list_blocking_ingredients_impl,
    )

    from tests.factories import make_manufacturing_order_recipe_row

    context, _, typed_cache = context_with_typed_cache
    _stub_variant_cache(context, {500: "WHEEL"})

    await seed_cache(
        typed_cache,
        [
            make_manufacturing_order(id=1, order_no="MO-1", status="DONE"),
            make_manufacturing_order(id=2, order_no="MO-2", status="IN_PROGRESS"),
            make_manufacturing_order_recipe_row(
                id=11,
                manufacturing_order_id=1,
                variant_id=500,
                ingredient_availability="NOT_AVAILABLE",
            ),
            make_manufacturing_order_recipe_row(
                id=12,
                manufacturing_order_id=2,
                variant_id=500,
                ingredient_availability="NOT_AVAILABLE",
            ),
        ],
    )

    result = await _list_blocking_ingredients_impl(
        ListBlockingIngredientsRequest(), context
    )

    assert result.total_blocking_rows == 1
    assert result.total_affected_mos == 1


@pytest.mark.asyncio
async def test_list_blocking_ingredients_excludes_deleted(
    context_with_typed_cache, no_sync_recipe_rows
):
    """Soft-deleted MOs and soft-deleted recipe rows are filtered out."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListBlockingIngredientsRequest,
        _list_blocking_ingredients_impl,
    )

    from tests.factories import make_manufacturing_order_recipe_row

    context, _, typed_cache = context_with_typed_cache
    _stub_variant_cache(context, {500: "WHEEL"})

    await seed_cache(
        typed_cache,
        [
            make_manufacturing_order(
                id=1,
                order_no="MO-DEL",
                status="IN_PROGRESS",
                deleted_at=datetime(2025, 1, 1, tzinfo=UTC),
            ),
            make_manufacturing_order(id=2, order_no="MO-LIVE", status="IN_PROGRESS"),
            make_manufacturing_order_recipe_row(
                id=11,
                manufacturing_order_id=1,
                variant_id=500,
                ingredient_availability="NOT_AVAILABLE",
            ),
            make_manufacturing_order_recipe_row(
                id=12,
                manufacturing_order_id=2,
                variant_id=500,
                ingredient_availability="NOT_AVAILABLE",
                deleted_at=datetime(2025, 1, 1, tzinfo=UTC),
            ),
        ],
    )

    result = await _list_blocking_ingredients_impl(
        ListBlockingIngredientsRequest(), context
    )

    assert result.total_blocking_rows == 0


@pytest.mark.asyncio
async def test_list_blocking_ingredients_groups_by_mo(
    context_with_typed_cache, no_sync_recipe_rows
):
    """group_by='mo' returns one block per affected MO with per-row detail."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListBlockingIngredientsRequest,
        _list_blocking_ingredients_impl,
    )

    from tests.factories import make_manufacturing_order_recipe_row

    context, _, typed_cache = context_with_typed_cache
    _stub_variant_cache(context, {500: "WHEEL", 600: "FORK"})

    await seed_cache(
        typed_cache,
        [
            make_manufacturing_order(id=1, order_no="MO-A", status="IN_PROGRESS"),
            make_manufacturing_order(id=2, order_no="MO-B", status="IN_PROGRESS"),
            make_manufacturing_order_recipe_row(
                id=11,
                manufacturing_order_id=1,
                variant_id=500,
                ingredient_availability="NOT_AVAILABLE",
            ),
            make_manufacturing_order_recipe_row(
                id=12,
                manufacturing_order_id=1,
                variant_id=600,
                ingredient_availability="EXPECTED",
            ),
            make_manufacturing_order_recipe_row(
                id=13,
                manufacturing_order_id=2,
                variant_id=500,
                ingredient_availability="NOT_AVAILABLE",
            ),
        ],
    )

    result = await _list_blocking_ingredients_impl(
        ListBlockingIngredientsRequest(group_by="mo"), context
    )

    assert result.by_variant is None
    assert result.by_mo is not None and len(result.by_mo) == 2
    by_id = {entry.manufacturing_order_id: entry for entry in result.by_mo}
    assert sorted(by_id.keys()) == [1, 2]
    assert len(by_id[1].blocking_rows) == 2
    assert len(by_id[2].blocking_rows) == 1


@pytest.mark.asyncio
async def test_list_blocking_ingredients_counts_mos_without_order_no(
    context_with_typed_cache, no_sync_recipe_rows
):
    """``affected_mo_count`` reflects every blocked MO even when ``order_no``
    is None — display lists only show populated order numbers, but the count
    must not be undercounted by missing display labels.
    """
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListBlockingIngredientsRequest,
        _list_blocking_ingredients_impl,
    )

    from tests.factories import make_manufacturing_order_recipe_row

    context, _, typed_cache = context_with_typed_cache
    _stub_variant_cache(context, {500: "WHEEL"})

    mo_with_order_no = make_manufacturing_order(
        id=1, order_no="MO-NUMBERED", status="IN_PROGRESS"
    )
    mo_no_order_no = make_manufacturing_order(id=2, order_no=None, status="IN_PROGRESS")
    await seed_cache(
        typed_cache,
        [
            mo_with_order_no,
            mo_no_order_no,
            make_manufacturing_order_recipe_row(
                id=11,
                manufacturing_order_id=1,
                variant_id=500,
                ingredient_availability="NOT_AVAILABLE",
            ),
            make_manufacturing_order_recipe_row(
                id=12,
                manufacturing_order_id=2,
                variant_id=500,
                ingredient_availability="NOT_AVAILABLE",
            ),
        ],
    )

    result = await _list_blocking_ingredients_impl(
        ListBlockingIngredientsRequest(), context
    )

    assert result.total_affected_mos == 2
    assert result.by_variant is not None and len(result.by_variant) == 1
    rollup = result.by_variant[0]
    assert rollup.affected_mo_count == 2
    assert rollup.affected_mo_order_nos == ["MO-NUMBERED"]


@pytest.mark.asyncio
async def test_list_blocking_ingredients_omits_recipe_rows_in_compact_json():
    """``include_rows='none'`` must drop the recipe_rows key from JSON."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        GetManufacturingOrderResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._get_manufacturing_order_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = GetManufacturingOrderResponse(
            id=3001, order_no="MO-X", status="IN_PROGRESS"
        )
        result = await get_manufacturing_order(
            order_id=3001, format="json", include_rows="none", context=context
        )

    data = json.loads(_content_text(result))
    assert "recipe_rows" not in data
    assert "operation_rows" not in data
    assert "productions" not in data


@pytest.mark.asyncio
async def test_list_blocking_ingredients_accepts_csv_order_nos():
    """``mo_order_nos`` accepts a CSV string via CoercedStrListOpt for LLM ergonomics."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListBlockingIngredientsRequest,
    )

    # CoercedStrListOpt's BeforeValidator accepts CSV/JSON strings as well as
    # bare lists; ``model_validate`` is the schema-boundary entry point that
    # exercises that coercion (the constructor is statically typed to list[str]).
    request = ListBlockingIngredientsRequest.model_validate(
        {"mo_order_nos": "MO-1,MO-2"}
    )
    assert request.mo_order_nos == ["MO-1", "MO-2"]


@pytest.mark.asyncio
async def test_list_blocking_ingredients_accepts_csv_status():
    """``mo_status`` accepts a CSV string the same way ``mo_order_nos`` does."""
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListBlockingIngredientsRequest,
    )

    request = ListBlockingIngredientsRequest.model_validate(
        {"mo_status": "NOT_STARTED,IN_PROGRESS"}
    )
    assert request.mo_status == ["NOT_STARTED", "IN_PROGRESS"]


@pytest.mark.asyncio
async def test_list_blocking_ingredients_resolves_skus_only_for_kept_variants(
    context_with_typed_cache, no_sync_recipe_rows
):
    """SKU lookups must happen *after* aggregation+slice so the legacy
    catalog cache only handles variants that actually appear in the response.

    Seeds two blocking variants (impact 1 and 2 MOs respectively); with
    ``limit=1`` only the higher-impact variant survives. Asserts that
    ``services.cache.get_by_id`` was awaited exactly once — for that variant.
    """
    from katana_mcp.tools.foundation.manufacturing_orders import (
        ListBlockingIngredientsRequest,
        _list_blocking_ingredients_impl,
    )

    from tests.factories import make_manufacturing_order_recipe_row

    context, _, typed_cache = context_with_typed_cache
    _stub_variant_cache(context, {500: "WHEEL", 600: "FORK"})

    await seed_cache(
        typed_cache,
        [
            make_manufacturing_order(id=1, order_no="MO-1", status="IN_PROGRESS"),
            make_manufacturing_order(id=2, order_no="MO-2", status="IN_PROGRESS"),
            # variant 500: blocked across both MOs (higher impact, kept)
            make_manufacturing_order_recipe_row(
                id=11,
                manufacturing_order_id=1,
                variant_id=500,
                ingredient_availability="NOT_AVAILABLE",
            ),
            make_manufacturing_order_recipe_row(
                id=12,
                manufacturing_order_id=2,
                variant_id=500,
                ingredient_availability="NOT_AVAILABLE",
            ),
            # variant 600: blocked on MO-1 only (lower impact, dropped by limit=1)
            make_manufacturing_order_recipe_row(
                id=13,
                manufacturing_order_id=1,
                variant_id=600,
                ingredient_availability="NOT_AVAILABLE",
            ),
        ],
    )

    result = await _list_blocking_ingredients_impl(
        ListBlockingIngredientsRequest(limit=1), context
    )

    # Only the higher-impact variant survives.
    assert result.by_variant is not None and len(result.by_variant) == 1
    assert result.by_variant[0].variant_id == 500
    assert result.by_variant[0].sku == "WHEEL"
    # Legacy cache batch helper called exactly once with only the kept
    # variant ID — the dropped variant 600 never makes it to the catalog
    # cache, validating slice-then-resolve over fetch-then-trim.
    cache_mock = context.request_context.lifespan_context.cache.get_many_by_ids
    assert cache_mock.await_count == 1
    awaited_vids = cache_mock.await_args.args[1]
    assert set(awaited_vids) == {500}


# ============================================================================
# modify_manufacturing_order — unified modification surface
# ============================================================================


_MODIFY_MO_UPDATE = (
    "katana_public_api_client.api.manufacturing_order.update_manufacturing_order"
)
_MODIFY_MO_DELETE = (
    "katana_public_api_client.api.manufacturing_order.delete_manufacturing_order"
)
_MODIFY_MO_RECIPE_CREATE = (
    "katana_public_api_client.api.manufacturing_order_recipe."
    "create_manufacturing_order_recipe_rows"
)
_MODIFY_MO_UNWRAP_AS = "katana_mcp.tools._modification_dispatch.unwrap_as"


def _mock_mo(mo_id: int = 1, order_no: str = "MO-1"):
    """Build a mock ManufacturingOrder with all fields defaulted to UNSET."""
    return mock_entity_for_modify(ManufacturingOrder, id=mo_id, order_no=order_no)


@pytest.mark.asyncio
async def test_modify_mo_requires_at_least_one_subpayload():
    context, _ = create_mock_context()
    with pytest.raises(ValueError, match="At least one sub-payload"):
        await _modify_manufacturing_order_impl(
            ModifyManufacturingOrderRequest(id=42, confirm=False), context
        )


@pytest.mark.asyncio
async def test_modify_mo_preview_emits_planned_actions():
    context, _ = create_mock_context()
    existing = _mock_mo(mo_id=42, order_no="MO-1")

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._fetch_manufacturing_order_attrs",
        new_callable=AsyncMock,
        return_value=existing,
    ):
        request = ModifyManufacturingOrderRequest(
            id=42,
            update_header=MOHeaderPatch(status="IN_PROGRESS"),
            add_recipe_rows=[
                MORecipeRowAdd(variant_id=100, planned_quantity_per_unit=2.0)
            ],
            confirm=False,
        )
        response = await _modify_manufacturing_order_impl(request, context)

    assert response.is_preview is True
    assert response.entity_id == 42
    assert len(response.actions) == 2
    assert response.actions[0].operation == "update_header"
    assert response.actions[1].operation == "add_recipe_row"
    assert all(a.succeeded is None for a in response.actions)


@pytest.mark.asyncio
async def test_modify_mo_confirm_executes_in_canonical_order():
    """Header → recipe adds → recipe updates → ..."""
    context, _ = create_mock_context()
    existing = _mock_mo(mo_id=42, order_no="MO-1")
    updated = _mock_mo(mo_id=42, order_no="MO-1")
    new_row = MagicMock()
    new_row.id = 555

    call_log: list[str] = []

    async def fake_update_mo(*, id, client, body):
        call_log.append("PATCH /manufacturing_orders/{id}")
        resp = MagicMock()
        resp.parsed = updated
        return resp

    async def fake_create_recipe(*, client, body):
        call_log.append("POST /manufacturing_order_recipe_rows")
        resp = MagicMock()
        resp.parsed = new_row
        return resp

    with (
        patch(
            "katana_mcp.tools.foundation.manufacturing_orders._fetch_manufacturing_order_attrs",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch(f"{_MODIFY_MO_UPDATE}.asyncio_detailed", side_effect=fake_update_mo),
        patch(
            f"{_MODIFY_MO_RECIPE_CREATE}.asyncio_detailed",
            side_effect=fake_create_recipe,
        ),
        patch(_MODIFY_MO_UNWRAP_AS, side_effect=[updated, new_row]),
    ):
        request = ModifyManufacturingOrderRequest(
            id=42,
            update_header=MOHeaderPatch(status="IN_PROGRESS"),
            add_recipe_rows=[
                MORecipeRowAdd(variant_id=100, planned_quantity_per_unit=2.0)
            ],
            confirm=True,
        )
        response = await _modify_manufacturing_order_impl(request, context)

    assert response.is_preview is False
    assert all(a.succeeded is True for a in response.actions)
    assert call_log[0].startswith("PATCH")
    assert call_log[1].startswith("POST")
    assert response.prior_state is not None


# ============================================================================
# delete_manufacturing_order
# ============================================================================


@pytest.mark.asyncio
async def test_delete_mo_preview_returns_planned_action():
    context, _ = create_mock_context()
    existing = _mock_mo(mo_id=42, order_no="MO-1")

    with patch(
        "katana_mcp.tools.foundation.manufacturing_orders._fetch_manufacturing_order_attrs",
        new_callable=AsyncMock,
        return_value=existing,
    ):
        response = await _delete_manufacturing_order_impl(
            DeleteManufacturingOrderRequest(id=42, confirm=False), context
        )

    assert response.is_preview is True
    assert response.entity_id == 42
    assert len(response.actions) == 1
    assert response.actions[0].operation == "delete"
    assert response.actions[0].succeeded is None


@pytest.mark.asyncio
async def test_delete_mo_confirm_calls_api_and_records_prior_state():
    context, _ = create_mock_context()
    existing = _mock_mo(mo_id=42, order_no="MO-1")
    api_response = MagicMock()
    api_response.status_code = 204

    with (
        patch(
            "katana_mcp.tools.foundation.manufacturing_orders._fetch_manufacturing_order_attrs",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch(
            f"{_MODIFY_MO_DELETE}.asyncio_detailed", new_callable=AsyncMock
        ) as mock_api,
        patch(
            "katana_mcp.tools._modification_dispatch.is_success",
            return_value=True,
        ),
    ):
        mock_api.return_value = api_response
        response = await _delete_manufacturing_order_impl(
            DeleteManufacturingOrderRequest(id=42, confirm=True), context
        )

    assert response.is_preview is False
    assert response.actions[0].succeeded is True
    assert response.prior_state is not None
    assert response.katana_url is None
    mock_api.assert_awaited_once()


# ============================================================================
# MO operation rows + production records — coverage gaps
# ============================================================================


_MODIFY_MO_OP_CREATE = (
    "katana_public_api_client.api.manufacturing_order_operation."
    "create_manufacturing_order_operation_row"
)
_MODIFY_MO_PROD_CREATE = (
    "katana_public_api_client.api.manufacturing_order_production."
    "create_manufacturing_order_production"
)


@pytest.mark.asyncio
async def test_modify_mo_operation_row_add_translates_status_and_type_enums():
    """Operation rows carry literal status + type that must convert to API enums.

    Exercises the ``_build_create_operation_row_request`` enum-conversion path.
    """
    context, _ = create_mock_context()
    existing = _mock_mo(mo_id=42, order_no="MO-1")
    new_op = MagicMock()
    new_op.id = 999

    captured_body = []

    async def fake_create_op(*, client, body):
        captured_body.append(body)
        resp = MagicMock()
        resp.parsed = new_op
        return resp

    with (
        patch(
            "katana_mcp.tools.foundation.manufacturing_orders._fetch_manufacturing_order_attrs",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch(f"{_MODIFY_MO_OP_CREATE}.asyncio_detailed", side_effect=fake_create_op),
        patch(_MODIFY_MO_UNWRAP_AS, return_value=new_op),
    ):
        request = ModifyManufacturingOrderRequest(
            id=42,
            add_operation_rows=[
                MOOperationRowAdd(
                    status="IN_PROGRESS",
                    type="perUnit",
                    operation_name="Cut to length",
                    planned_time_per_unit=2.5,
                ),
            ],
            confirm=True,
        )
        response = await _modify_manufacturing_order_impl(request, context)

    assert response.is_preview is False
    assert len(response.actions) == 1
    assert response.actions[0].operation == "add_operation_row"
    # Verify the API body has the actual API enum members, not strings
    from katana_public_api_client.models import (
        ManufacturingOperationStatus,
        ManufacturingOperationType,
    )

    body = captured_body[0]
    assert body.status == ManufacturingOperationStatus.IN_PROGRESS
    assert body.type_ == ManufacturingOperationType.PERUNIT
    assert body.operation_name == "Cut to length"
    assert body.planned_time_per_unit == 2.5


@pytest.mark.asyncio
async def test_modify_mo_production_record_add_passes_through_to_api():
    """Production records have a small-but-distinct shape; cover the
    add path end-to-end."""
    context, _ = create_mock_context()
    existing = _mock_mo(mo_id=42, order_no="MO-1")
    new_prod = MagicMock()
    new_prod.id = 7777

    captured_body = []

    async def fake_create_prod(*, client, body):
        captured_body.append(body)
        resp = MagicMock()
        resp.parsed = new_prod
        return resp

    with (
        patch(
            "katana_mcp.tools.foundation.manufacturing_orders._fetch_manufacturing_order_attrs",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch(
            f"{_MODIFY_MO_PROD_CREATE}.asyncio_detailed",
            side_effect=fake_create_prod,
        ),
        patch(_MODIFY_MO_UNWRAP_AS, return_value=new_prod),
    ):
        request = ModifyManufacturingOrderRequest(
            id=42,
            add_productions=[
                MOProductionAdd(
                    completed_quantity=10.0,
                    is_final=True,
                    serial_numbers=["SN-001", "SN-002"],
                ),
            ],
            confirm=True,
        )
        response = await _modify_manufacturing_order_impl(request, context)

    assert response.is_preview is False
    assert response.actions[0].operation == "add_production"
    body = captured_body[0]
    assert body.manufacturing_order_id == 42
    assert body.completed_quantity == 10.0
    assert body.is_final is True
    assert body.serial_numbers == ["SN-001", "SN-002"]


@pytest.mark.asyncio
async def test_modify_mo_canonical_order_across_all_three_sub_resources():
    """Header + recipe row + operation row + production all in one call,
    confirming canonical execution order across all three sub-resource kinds."""
    context, _ = create_mock_context()
    existing = _mock_mo(mo_id=42, order_no="MO-1")
    updated = _mock_mo(mo_id=42, order_no="MO-1")
    new_recipe = MagicMock()
    new_recipe.id = 100
    new_op = MagicMock()
    new_op.id = 200
    new_prod = MagicMock()
    new_prod.id = 300

    call_log: list[str] = []

    async def fake_update_mo(*, id, client, body):
        call_log.append("update_header")
        resp = MagicMock()
        resp.parsed = updated
        return resp

    async def fake_create_recipe(*, client, body):
        call_log.append("add_recipe_row")
        resp = MagicMock()
        resp.parsed = new_recipe
        return resp

    async def fake_create_op(*, client, body):
        call_log.append("add_operation_row")
        resp = MagicMock()
        resp.parsed = new_op
        return resp

    async def fake_create_prod(*, client, body):
        call_log.append("add_production")
        resp = MagicMock()
        resp.parsed = new_prod
        return resp

    with (
        patch(
            "katana_mcp.tools.foundation.manufacturing_orders._fetch_manufacturing_order_attrs",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch(f"{_MODIFY_MO_UPDATE}.asyncio_detailed", side_effect=fake_update_mo),
        patch(
            f"{_MODIFY_MO_RECIPE_CREATE}.asyncio_detailed",
            side_effect=fake_create_recipe,
        ),
        patch(f"{_MODIFY_MO_OP_CREATE}.asyncio_detailed", side_effect=fake_create_op),
        patch(
            f"{_MODIFY_MO_PROD_CREATE}.asyncio_detailed",
            side_effect=fake_create_prod,
        ),
        patch(
            _MODIFY_MO_UNWRAP_AS,
            side_effect=[updated, new_recipe, new_op, new_prod],
        ),
    ):
        request = ModifyManufacturingOrderRequest(
            id=42,
            update_header=MOHeaderPatch(status="IN_PROGRESS"),
            add_recipe_rows=[
                MORecipeRowAdd(variant_id=100, planned_quantity_per_unit=2.0)
            ],
            add_operation_rows=[
                MOOperationRowAdd(status="NOT_STARTED", operation_name="Assembly")
            ],
            add_productions=[MOProductionAdd(completed_quantity=5.0)],
            confirm=True,
        )
        response = await _modify_manufacturing_order_impl(request, context)

    assert response.is_preview is False
    assert len(response.actions) == 4
    assert all(a.succeeded is True for a in response.actions)
    # Canonical order: header → recipe → operation → production
    assert call_log == [
        "update_header",
        "add_recipe_row",
        "add_operation_row",
        "add_production",
    ]
