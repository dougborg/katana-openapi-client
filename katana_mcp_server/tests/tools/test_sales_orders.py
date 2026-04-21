"""Tests for sales order MCP tools."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.sales_orders import (
    CreateSalesOrderRequest,
    GetSalesOrderRequest,
    ListSalesOrdersRequest,
    SalesOrderAddress,
    SalesOrderItem,
    _create_sales_order_impl,
    _get_sales_order_impl,
    _list_sales_orders_impl,
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


# ============================================================================
# list_sales_orders tests
# ============================================================================

_SO_GET_ALL = "katana_public_api_client.api.sales_order.get_all_sales_orders"
_SO_GET = "katana_public_api_client.api.sales_order.get_sales_order"
_SO_UNWRAP_DATA = "katana_public_api_client.utils.unwrap_data"
_SO_UNWRAP_AS = "katana_public_api_client.utils.unwrap_as"


def _make_mock_so(
    *,
    id: int = 12345,
    order_no: str = "SO-TEST",
    customer_id: int = 42,
    location_id: int = 1,
    status: str = "PENDING",
    production_status: str = "NONE",
    total: float | None = 999.0,
    currency: str = "USD",
    rows: list | None = None,
) -> MagicMock:
    """Build a mock SalesOrder attrs object for testing."""
    so = MagicMock()
    so.id = id
    so.order_no = order_no
    so.customer_id = customer_id
    so.location_id = location_id
    so.status = status
    so.production_status = production_status
    so.invoicing_status = UNSET
    so.created_at = datetime(2026, 4, 10, 9, 0, tzinfo=UTC)
    so.delivery_date = datetime(2026, 4, 20, 12, 0, tzinfo=UTC)
    so.total = total
    so.currency = currency
    so.additional_info = UNSET
    so.sales_order_rows = rows if rows is not None else []
    return so


def _make_mock_row(
    *,
    id: int,
    variant_id: int,
    quantity: float,
    price_per_unit: float,
    linked_mo_id: int | None = None,
) -> MagicMock:
    """Build a mock sales order row."""
    r = MagicMock()
    r.id = id
    r.variant_id = variant_id
    r.quantity = quantity
    r.price_per_unit = price_per_unit
    r.linked_manufacturing_order_id = (
        linked_mo_id if linked_mo_id is not None else UNSET
    )
    return r


@pytest.mark.asyncio
async def test_list_sales_orders_passes_explicit_filters():
    """All explicit non-None filters end up in the API kwargs."""
    context, _ = create_mock_context()
    captured_kwargs: dict = {}

    async def fake_asyncio_detailed(**kwargs):
        captured_kwargs.update(kwargs)
        return MagicMock()

    request = ListSalesOrdersRequest(
        order_no="SO-100",
        customer_id=42,
        location_id=7,
        status="PENDING",
        limit=25,
    )

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", side_effect=fake_asyncio_detailed),
        patch(_SO_UNWRAP_DATA, return_value=[]),
    ):
        result = await _list_sales_orders_impl(request, context)

    assert captured_kwargs["order_no"] == "SO-100"
    assert captured_kwargs["customer_id"] == 42
    assert captured_kwargs["location_id"] == 7
    assert captured_kwargs["status"] == "PENDING"
    assert captured_kwargs["limit"] == 25
    assert "production_status" not in captured_kwargs
    assert result.total_count == 0


@pytest.mark.asyncio
async def test_list_sales_orders_zero_valued_filters_are_passed_through():
    """customer_id=0 / location_id=0 must be passed as filters, not dropped."""
    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    request = ListSalesOrdersRequest(customer_id=0, location_id=0)

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", side_effect=fake),
        patch(_SO_UNWRAP_DATA, return_value=[]),
    ):
        await _list_sales_orders_impl(request, context)

    assert captured["customer_id"] == 0
    assert captured["location_id"] == 0


@pytest.mark.asyncio
async def test_list_sales_orders_needs_work_orders_shortcut():
    """needs_work_orders=True sets production_status=NONE."""
    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    request = ListSalesOrdersRequest(needs_work_orders=True)

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", side_effect=fake),
        patch(_SO_UNWRAP_DATA, return_value=[]),
    ):
        await _list_sales_orders_impl(request, context)

    assert captured["production_status"] == "NONE"


@pytest.mark.asyncio
async def test_list_sales_orders_explicit_production_status_wins_over_shortcut():
    """Explicit production_status overrides needs_work_orders=True."""
    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    request = ListSalesOrdersRequest(
        production_status="IN_PROGRESS",
        needs_work_orders=True,
    )

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", side_effect=fake),
        patch(_SO_UNWRAP_DATA, return_value=[]),
    ):
        await _list_sales_orders_impl(request, context)

    assert captured["production_status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_list_sales_orders_caps_results_to_request_limit():
    """Regression for #329: even if transport returns more rows than asked,
    the response is sliced to request.limit."""
    context, _ = create_mock_context()

    # Simulate transport returning way more rows than requested (this is the
    # #329 symptom: auto-pagination flooded the response).
    over_fetched = [_make_mock_so(id=i, order_no=f"SO-{i}") for i in range(200)]

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_SO_UNWRAP_DATA, return_value=over_fetched),
    ):
        request = ListSalesOrdersRequest(limit=50)
        result = await _list_sales_orders_impl(request, context)

    assert len(result.orders) == 50
    assert result.total_count == 50


@pytest.mark.asyncio
async def test_list_sales_orders_passes_page_1_when_limit_fits_single_page():
    """Regression for #329: when limit <= 250 (Katana page max), pass page=1
    so PaginationTransport skips auto-pagination."""
    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    request = ListSalesOrdersRequest(limit=10)

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", side_effect=fake),
        patch(_SO_UNWRAP_DATA, return_value=[]),
    ):
        await _list_sales_orders_impl(request, context)

    assert captured["page"] == 1
    assert captured["limit"] == 10


@pytest.mark.asyncio
async def test_list_sales_orders_omits_page_when_limit_exceeds_single_page():
    """For limit > 250, let auto-pagination do its thing (no explicit page)."""
    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    request = ListSalesOrdersRequest(limit=500)

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", side_effect=fake),
        patch(_SO_UNWRAP_DATA, return_value=[]),
    ):
        await _list_sales_orders_impl(request, context)

    assert "page" not in captured
    assert captured["limit"] == 500


@pytest.mark.asyncio
async def test_list_sales_orders_returns_summary_rows():
    """Response rows carry order_no, totals, and row_count."""
    context, _ = create_mock_context()
    mock_so = _make_mock_so(
        id=42,
        order_no="SO-42",
        total=1234.56,
        rows=[
            _make_mock_row(id=1, variant_id=100, quantity=2, price_per_unit=500.0),
            _make_mock_row(id=2, variant_id=101, quantity=1, price_per_unit=234.56),
        ],
    )

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_SO_UNWRAP_DATA, return_value=[mock_so]),
    ):
        result = await _list_sales_orders_impl(ListSalesOrdersRequest(), context)

    assert result.total_count == 1
    assert result.orders[0].id == 42
    assert result.orders[0].order_no == "SO-42"
    assert result.orders[0].total == 1234.56
    assert result.orders[0].row_count == 2


@pytest.mark.asyncio
async def test_list_sales_orders_page_forwards_and_parses_header():
    """Explicit page forwards to API and x-pagination header populates PaginationMeta."""
    context, _ = create_mock_context()
    captured: dict = {}

    # Build a response that carries the Katana `x-pagination` header format.
    mock_response = MagicMock()
    mock_response.headers = {
        "x-pagination": (
            '{"total_records":"100","total_pages":"2","offset":"0","page":"1",'
            '"first_page":"true","last_page":"false"}'
        )
    }

    async def fake_asyncio_detailed(**kwargs):
        captured.update(kwargs)
        return mock_response

    request = ListSalesOrdersRequest(page=1, limit=50)

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", side_effect=fake_asyncio_detailed),
        patch(_SO_UNWRAP_DATA, return_value=[]),
    ):
        result = await _list_sales_orders_impl(request, context)

    # Explicit page was forwarded to the API (which disables auto-pagination).
    assert captured["page"] == 1
    assert captured["limit"] == 50

    assert result.pagination is not None
    assert result.pagination.total_records == 100
    assert result.pagination.total_pages == 2
    assert result.pagination.page == 1
    assert result.pagination.first_page is True
    assert result.pagination.last_page is False


@pytest.mark.asyncio
async def test_list_sales_orders_no_page_leaves_pagination_none():
    """When caller did not pass `page`, response.pagination stays None even
    if the underlying request short-circuited with page=1 and the transport
    passed through an `x-pagination` header — that header describes a single
    internal page and would be misleading to surface to the caller."""
    context, _ = create_mock_context()
    captured: dict = {}

    mock_response = MagicMock()
    mock_response.headers = {
        "x-pagination": (
            '{"total_records":"100","total_pages":"2","offset":"0","page":"1",'
            '"first_page":"true","last_page":"false"}'
        )
    }

    async def fake_asyncio_detailed(**kwargs):
        captured.update(kwargs)
        return mock_response

    # limit=50 <= 250 triggers the short-circuit that forwards page=1
    # internally (see #329). We still must not surface pagination metadata
    # because the *caller* did not request a specific page.
    request = ListSalesOrdersRequest(limit=50)

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", side_effect=fake_asyncio_detailed),
        patch(_SO_UNWRAP_DATA, return_value=[]),
    ):
        result = await _list_sales_orders_impl(request, context)

    # Short-circuit forwards page=1 internally, but pagination metadata is
    # gated on the *request's* page field, not what we sent to the API.
    assert captured["page"] == 1
    assert result.pagination is None


# ============================================================================
# get_sales_order tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_sales_order_requires_identifier():
    """Must provide order_no or order_id."""
    context, _ = create_mock_context()

    request = GetSalesOrderRequest()
    with pytest.raises(ValueError, match="order_no or order_id"):
        await _get_sales_order_impl(request, context)


@pytest.mark.asyncio
async def test_get_sales_order_by_id():
    """Look up by order_id via api_get_sales_order → unwrap_as."""
    context, _ = create_mock_context()
    mock_so = _make_mock_so(
        id=777,
        order_no="SO-777",
        rows=[_make_mock_row(id=10, variant_id=500, quantity=3, price_per_unit=99.0)],
    )

    with (
        patch(f"{_SO_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_SO_UNWRAP_AS, return_value=mock_so),
    ):
        request = GetSalesOrderRequest(order_id=777)
        result = await _get_sales_order_impl(request, context)

    assert result.id == 777
    assert result.order_no == "SO-777"
    assert len(result.rows) == 1
    assert result.rows[0].id == 10
    assert result.rows[0].variant_id == 500
    assert result.rows[0].quantity == 3


@pytest.mark.asyncio
async def test_get_sales_order_by_number():
    """Look up by order_no via get_all_sales_orders → unwrap_data → first row."""
    context, _ = create_mock_context()
    mock_so = _make_mock_so(id=5, order_no="#WEB20394")

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_SO_UNWRAP_DATA, return_value=[mock_so]),
    ):
        request = GetSalesOrderRequest(order_no="#WEB20394")
        result = await _get_sales_order_impl(request, context)

    assert result.id == 5
    assert result.order_no == "#WEB20394"


@pytest.mark.asyncio
async def test_get_sales_order_not_found_by_number_raises():
    """Empty results from get_all_sales_orders raises ValueError."""
    context, _ = create_mock_context()

    with (
        patch(f"{_SO_GET_ALL}.asyncio_detailed", new_callable=AsyncMock),
        patch(_SO_UNWRAP_DATA, return_value=[]),
    ):
        request = GetSalesOrderRequest(order_no="#MISSING")
        with pytest.raises(ValueError, match="'#MISSING' not found"):
            await _get_sales_order_impl(request, context)


@pytest.mark.asyncio
async def test_get_sales_order_enriches_row_sku_from_cache():
    """Row-level variant cache hits populate SalesOrderRowInfo.sku."""
    context, lifespan_ctx = create_mock_context()

    # Cache returns a variant dict for variant_id 500
    async def fake_get_by_id(_entity_type, variant_id):
        if variant_id == 500:
            return {"id": 500, "sku": "BIKE-A", "display_name": "Bike A"}
        return None

    lifespan_ctx.cache.get_by_id = AsyncMock(side_effect=fake_get_by_id)

    mock_so = _make_mock_so(
        id=9,
        rows=[
            _make_mock_row(id=1, variant_id=500, quantity=1, price_per_unit=100),
            _make_mock_row(id=2, variant_id=999, quantity=1, price_per_unit=50),
        ],
    )

    with (
        patch(f"{_SO_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_SO_UNWRAP_AS, return_value=mock_so),
    ):
        result = await _get_sales_order_impl(GetSalesOrderRequest(order_id=9), context)

    assert result.rows[0].sku == "BIKE-A"  # cache hit
    assert result.rows[1].sku is None  # cache miss
