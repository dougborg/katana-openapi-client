"""Tests for sales order MCP tools."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.tools.foundation.sales_orders import (
    CreateSalesOrderRequest,
    SalesOrderAddress,
    SalesOrderItem,
    _create_sales_order_impl,
)

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    SalesOrder,
    SalesOrderStatus,
)
from katana_public_api_client.utils import APIError
from tests.conftest import create_mock_context

# ============================================================================
# Unit Tests (with mocks)
# ============================================================================


@pytest.mark.asyncio
async def test_create_sales_order_preview():
    """Test create_sales_order in preview mode."""
    context, _ = create_mock_context()

    request = CreateSalesOrderRequest(
        customer_id=1501,
        order_number="SO-2024-001",
        items=[
            SalesOrderItem(variant_id=2101, quantity=3, price_per_unit=599.99),
            SalesOrderItem(variant_id=2102, quantity=2, price_per_unit=149.99),
        ],
        location_id=1,
        delivery_date=datetime(2024, 1, 22, 14, 0, 0, tzinfo=UTC),
        currency="USD",
        notes="Test order",
        customer_ref="CUST-REF-001",
        confirm=False,
    )
    result = await _create_sales_order_impl(request, context)

    assert result.is_preview is True
    assert result.customer_id == 1501
    assert result.order_number == "SO-2024-001"
    assert result.location_id == 1
    assert result.currency == "USD"
    assert result.status == "PENDING"
    assert result.id is None
    assert "preview" in result.message.lower()
    assert len(result.next_actions) > 0
    assert len(result.warnings) == 0  # All optional fields provided
    # Verify total calculation: (3 * 599.99) + (2 * 149.99) = 1799.97 + 299.98 = 2099.95
    assert result.total == pytest.approx(2099.95, rel=0.01)


@pytest.mark.asyncio
async def test_create_sales_order_preview_minimal_fields():
    """Test create_sales_order preview with only required fields."""
    context, _ = create_mock_context()

    request = CreateSalesOrderRequest(
        customer_id=1501,
        order_number="SO-2024-002",
        items=[
            SalesOrderItem(variant_id=2101, quantity=1),
        ],
        confirm=False,
    )
    result = await _create_sales_order_impl(request, context)

    assert result.is_preview is True
    assert result.customer_id == 1501
    assert result.order_number == "SO-2024-002"
    assert result.location_id is None
    assert result.currency is None
    assert result.delivery_date is None
    # Verify warnings for missing optional fields
    assert len(result.warnings) == 2
    assert any("location_id" in w for w in result.warnings)
    assert any("delivery_date" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_create_sales_order_confirm_success():
    """Test create_sales_order with confirm=True succeeds."""
    context, _lifespan_ctx = create_mock_context()

    # Mock successful API response
    # Note: SalesOrderStatus uses NOT_SHIPPED as starting status, not PENDING
    mock_so = SalesOrder(
        id=2001,
        customer_id=1501,
        order_no="SO-2024-001",
        location_id=1,
        status=SalesOrderStatus.NOT_SHIPPED,
        currency="USD",
        total=1799.97,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_so

    # Mock the API call
    mock_api_call = AsyncMock(return_value=mock_response)

    # Patch the API call
    import katana_public_api_client.api.sales_order.create_sales_order as create_so_module

    original_asyncio_detailed = create_so_module.asyncio_detailed
    create_so_module.asyncio_detailed = mock_api_call

    try:
        request = CreateSalesOrderRequest(
            customer_id=1501,
            order_number="SO-2024-001",
            items=[
                SalesOrderItem(variant_id=2101, quantity=3, price_per_unit=599.99),
            ],
            location_id=1,
            currency="USD",
            confirm=True,
        )
        result = await _create_sales_order_impl(request, context)

        assert result.is_preview is False
        assert result.id == 2001
        assert result.order_number == "SO-2024-001"
        assert result.customer_id == 1501
        assert result.location_id == 1
        assert result.status == "NOT_SHIPPED"
        assert result.currency == "USD"
        assert result.total == 1799.97
        assert "2001" in result.message
        assert len(result.next_actions) > 0

        # Verify API was called
        mock_api_call.assert_called_once()
    finally:
        # Restore original function
        create_so_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_sales_order_with_addresses():
    """Test create_sales_order with billing and shipping addresses."""
    context, _lifespan_ctx = create_mock_context()

    # Mock successful API response
    mock_so = SalesOrder(
        id=2002,
        customer_id=1501,
        order_no="SO-2024-003",
        location_id=1,
        status=SalesOrderStatus.NOT_SHIPPED,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_so

    mock_api_call = AsyncMock(return_value=mock_response)

    import katana_public_api_client.api.sales_order.create_sales_order as create_so_module

    original_asyncio_detailed = create_so_module.asyncio_detailed
    create_so_module.asyncio_detailed = mock_api_call

    try:
        request = CreateSalesOrderRequest(
            customer_id=1501,
            order_number="SO-2024-003",
            items=[
                SalesOrderItem(variant_id=2101, quantity=1, price_per_unit=99.99),
            ],
            location_id=1,
            addresses=[
                SalesOrderAddress(
                    entity_type="billing",
                    first_name="John",
                    last_name="Doe",
                    company="Acme Corp",
                    line_1="123 Main St",
                    city="Portland",
                    state="OR",
                    zip_code="97201",
                    country="US",
                ),
                SalesOrderAddress(
                    entity_type="shipping",
                    first_name="Jane",
                    last_name="Doe",
                    line_1="456 Oak Ave",
                    city="Seattle",
                    state="WA",
                    zip_code="98101",
                    country="US",
                ),
            ],
            confirm=True,
        )
        result = await _create_sales_order_impl(request, context)

        assert result.is_preview is False
        assert result.id == 2002
        mock_api_call.assert_called_once()

        # Verify addresses were passed to API
        call_kwargs = mock_api_call.call_args.kwargs
        api_request = call_kwargs["body"]
        assert not isinstance(api_request.addresses, type(UNSET))
        assert len(api_request.addresses) == 2
    finally:
        create_so_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_sales_order_with_discount():
    """Test create_sales_order with line item discounts."""
    context, _ = create_mock_context()

    request = CreateSalesOrderRequest(
        customer_id=1501,
        order_number="SO-2024-004",
        items=[
            SalesOrderItem(
                variant_id=2101,
                quantity=10,
                price_per_unit=100.0,
                total_discount=50.0,
            ),
        ],
        confirm=False,
    )
    result = await _create_sales_order_impl(request, context)

    assert result.is_preview is True
    # Total should be (10 * 100) - 50 = 950
    assert result.total == pytest.approx(950.0, rel=0.01)


@pytest.mark.asyncio
async def test_create_sales_order_api_error():
    """Test create_sales_order handles API errors."""
    context, _lifespan_ctx = create_mock_context()

    # Mock error response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.parsed = None

    mock_api_call = AsyncMock(return_value=mock_response)

    import katana_public_api_client.api.sales_order.create_sales_order as create_so_module

    original_asyncio_detailed = create_so_module.asyncio_detailed
    create_so_module.asyncio_detailed = mock_api_call

    try:
        request = CreateSalesOrderRequest(
            customer_id=1501,
            order_number="SO-2024-005",
            items=[
                SalesOrderItem(variant_id=2101, quantity=1),
            ],
            confirm=True,
        )

        with pytest.raises(APIError):
            await _create_sales_order_impl(request, context)
    finally:
        create_so_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_sales_order_api_exception():
    """Test create_sales_order handles API exceptions."""
    context, _lifespan_ctx = create_mock_context()

    # Mock API call that raises exception
    mock_api_call = AsyncMock(side_effect=Exception("Network error"))

    import katana_public_api_client.api.sales_order.create_sales_order as create_so_module

    original_asyncio_detailed = create_so_module.asyncio_detailed
    create_so_module.asyncio_detailed = mock_api_call

    try:
        request = CreateSalesOrderRequest(
            customer_id=1501,
            order_number="SO-2024-006",
            items=[
                SalesOrderItem(variant_id=2101, quantity=1),
            ],
            confirm=True,
        )

        with pytest.raises(Exception, match="Network error"):
            await _create_sales_order_impl(request, context)
    finally:
        create_so_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_sales_order_confirm_with_minimal_fields():
    """Test create_sales_order with only required fields."""
    context, _lifespan_ctx = create_mock_context()

    # Mock successful API response with minimal fields
    mock_so = SalesOrder(
        id=2003,
        customer_id=1501,
        order_no="SO-2024-007",
        location_id=1,
        status=SalesOrderStatus.NOT_SHIPPED,
        currency=UNSET,
        total=UNSET,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_so

    mock_api_call = AsyncMock(return_value=mock_response)

    import katana_public_api_client.api.sales_order.create_sales_order as create_so_module

    original_asyncio_detailed = create_so_module.asyncio_detailed
    create_so_module.asyncio_detailed = mock_api_call

    try:
        request = CreateSalesOrderRequest(
            customer_id=1501,
            order_number="SO-2024-007",
            items=[
                SalesOrderItem(variant_id=2101, quantity=1),
            ],
            confirm=True,
        )
        result = await _create_sales_order_impl(request, context)

        assert result.is_preview is False
        assert result.id == 2003
        assert result.order_number == "SO-2024-007"
        assert result.customer_id == 1501
        assert result.currency is None
        assert result.total is None
    finally:
        create_so_module.asyncio_detailed = original_asyncio_detailed


@pytest.mark.asyncio
async def test_create_sales_order_user_declines():
    """Test create_sales_order when user declines elicitation."""
    # Create context with elicit_confirm=False to simulate user declining
    context, _ = create_mock_context(elicit_confirm=False)

    request = CreateSalesOrderRequest(
        customer_id=1501,
        order_number="SO-2024-011",
        items=[
            SalesOrderItem(variant_id=2101, quantity=1, price_per_unit=99.99),
        ],
        confirm=True,
    )
    result = await _create_sales_order_impl(request, context)

    # User declined, so it should return preview mode with cancellation message
    assert result.is_preview is True
    assert result.id is None
    assert result.order_number == "SO-2024-011"
    assert result.customer_id == 1501
    assert "cancelled" in result.message.lower()
    assert len(result.next_actions) > 0


# ============================================================================
# Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_sales_order_invalid_quantity():
    """Test create_sales_order rejects invalid quantity."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateSalesOrderRequest(
            customer_id=1501,
            order_number="SO-2024-008",
            items=[
                SalesOrderItem(variant_id=2101, quantity=0.0),  # Invalid: must be > 0
            ],
            confirm=False,
        )


@pytest.mark.asyncio
async def test_create_sales_order_negative_quantity():
    """Test create_sales_order rejects negative quantity."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateSalesOrderRequest(
            customer_id=1501,
            order_number="SO-2024-009",
            items=[
                SalesOrderItem(variant_id=2101, quantity=-5.0),  # Invalid: must be > 0
            ],
            confirm=False,
        )


@pytest.mark.asyncio
async def test_create_sales_order_empty_items():
    """Test create_sales_order rejects empty items list."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateSalesOrderRequest(
            customer_id=1501,
            order_number="SO-2024-010",
            items=[],  # Invalid: min_length=1
            confirm=False,
        )


# ============================================================================
# Integration Tests (with real API)
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_sales_order_preview_integration(katana_context):
    """Integration test: create_sales_order preview with real Katana API.

    This test requires a valid KATANA_API_KEY in the environment.
    Tests preview mode which doesn't make API calls.
    """
    request = CreateSalesOrderRequest(
        customer_id=1501,
        order_number="SO-INT-TEST-001",
        items=[
            SalesOrderItem(variant_id=2101, quantity=1, price_per_unit=99.99),
        ],
        location_id=1,
        delivery_date=datetime(2024, 12, 31, 17, 0, 0, tzinfo=UTC),
        notes="Integration test preview",
        confirm=False,
    )

    try:
        result = await _create_sales_order_impl(request, katana_context)

        # Verify response structure
        assert result.is_preview is True
        assert result.customer_id == 1501
        assert result.order_number == "SO-INT-TEST-001"
        assert isinstance(result.message, str)
        assert isinstance(result.next_actions, list)
        assert result.id is None  # Preview mode doesn't create
    except Exception as e:
        # Should not fail in preview mode
        pytest.fail(f"Preview mode should not fail: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_sales_order_confirm_integration(katana_context):
    """Integration test: create_sales_order confirm with real Katana API.

    This test requires a valid KATANA_API_KEY in the environment.
    Tests actual creation of sales order.

    Note: This test may fail if:
    - API key is invalid
    - Network is unavailable
    - Customer doesn't exist
    - Variant doesn't exist
    - Location doesn't exist
    """
    request = CreateSalesOrderRequest(
        customer_id=1501,
        order_number=f"SO-INT-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
        items=[
            SalesOrderItem(variant_id=2101, quantity=1, price_per_unit=99.99),
        ],
        location_id=1,
        notes="Integration test - can be deleted",
        confirm=True,
    )

    try:
        result = await _create_sales_order_impl(request, katana_context)

        # Verify response structure
        assert result.is_preview is False
        assert isinstance(result.id, int)
        assert result.id > 0
        assert isinstance(result.order_number, str)
        assert result.customer_id == 1501
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
                "customer",
                "variant",
                "location",
                "invalid",
            ]
        ), f"Unexpected error: {e}"
