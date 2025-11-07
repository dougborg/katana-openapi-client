"""Tests for manufacturing order MCP tools."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.tools.foundation.manufacturing_orders import (
    CreateManufacturingOrderRequest,
    _create_manufacturing_order_impl,
)

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    ManufacturingOrder,
    ManufacturingOrderStatus,
)

# ============================================================================
# Test Helpers
# ============================================================================


def create_mock_context():
    """Create a mock context with proper FastMCP structure.

    Returns context with request_context.lifespan_context.client accessible.
    """
    context = MagicMock()
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()
    context.request_context = mock_request_context
    mock_request_context.lifespan_context = mock_lifespan_context
    return context, mock_lifespan_context


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
    context, lifespan_ctx = create_mock_context()

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
    context, lifespan_ctx = create_mock_context()

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
    context, lifespan_ctx = create_mock_context()

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

        with pytest.raises(Exception, match="API returned unexpected status"):
            await _create_manufacturing_order_impl(request, context)
    finally:
        # Restore original function
        create_mo_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_manufacturing_order_api_exception():
    """Test create_manufacturing_order handles API exceptions."""
    context, lifespan_ctx = create_mock_context()

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
