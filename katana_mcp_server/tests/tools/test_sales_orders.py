"""Tests for sales order MCP tools."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.sales_orders import (
    CreateSalesOrderRequest,
    DeleteSalesOrderRequest,
    GetSalesOrderRequest,
    ListSalesOrdersRequest,
    ModifySalesOrderRequest,
    SalesOrderAddress,
    SalesOrderItem,
    SOHeaderPatch,
    SORowAdd,
    _create_sales_order_impl,
    _delete_sales_order_impl,
    _get_sales_order_impl,
    _list_sales_orders_impl,
    _modify_sales_order_impl,
    get_sales_order,
    list_sales_orders,
)

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    SalesOrder,
    SalesOrderStatus,
)
from katana_public_api_client.utils import APIError
from tests.conftest import create_mock_context, patch_typed_cache_sync
from tests.factories import (
    make_sales_order,
    make_sales_order_row,
    mock_entity_for_modify,
    seed_cache,
)

# ============================================================================
# Unit Tests (with mocks)
# ============================================================================


@pytest.mark.asyncio
async def test_create_sales_order_preview():
    """Test create_sales_order in preview mode."""
    context, lifespan_ctx = create_mock_context()
    # Seed customer cache so the BLOCK warning for missing customer doesn't fire.
    lifespan_ctx.cache.get_by_id = AsyncMock(return_value={"id": 1501, "name": "Acme"})

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
        preview=True,
    )
    result = await _create_sales_order_impl(request, context)

    assert result.is_preview is True
    assert result.customer_id == 1501
    assert result.customer_name == "Acme"
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
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_id = AsyncMock(return_value={"id": 1501, "name": "Acme"})

    request = CreateSalesOrderRequest(
        customer_id=1501,
        order_number="SO-2024-002",
        items=[
            SalesOrderItem(variant_id=2101, quantity=1),
        ],
        preview=True,
    )
    result = await _create_sales_order_impl(request, context)

    assert result.is_preview is True
    assert result.customer_id == 1501
    assert result.order_number == "SO-2024-002"
    assert result.location_id is None
    assert result.currency is None
    assert result.delivery_date is None
    # Verify warnings for missing optional fields (BLOCK warnings excluded
    # since customer was found in cache).
    non_block = [w for w in result.warnings if not w.startswith("BLOCK:")]
    assert len(non_block) == 2
    assert any("location_id" in w for w in non_block)
    assert any("delivery_date" in w for w in non_block)


@pytest.mark.asyncio
async def test_create_sales_order_preview_warns_advisorily_on_customer_cache_miss():
    """Customer cache miss should emit an advisory (non-BLOCK) warning.

    Cache lag is legitimate — a customer created moments ago in Katana may
    not yet be cached locally — so the live API is the authority on whether
    the customer exists. The preview surfaces the cache miss so the user
    knows we couldn't pretty-print the name, but the Confirm button stays
    available; the live API will reject the call if the customer is
    genuinely bad.
    """
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_id = AsyncMock(return_value=None)

    request = CreateSalesOrderRequest(
        customer_id=99999,
        order_number="SO-X",
        items=[SalesOrderItem(variant_id=1, quantity=1)],
        location_id=1,
        delivery_date=datetime(2024, 1, 22, 14, 0, 0, tzinfo=UTC),
        preview=True,
    )
    result = await _create_sales_order_impl(request, context)

    assert result.is_preview is True
    assert result.customer_name is None
    # Cache miss yields an advisory warning, NOT a BLOCK.
    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert len(block_warnings) == 0, (
        "Cache miss must not BLOCK — cache lag is legitimate"
    )
    advisory = [w for w in result.warnings if "99999" in w and "cache" in w.lower()]
    assert len(advisory) == 1


@pytest.mark.asyncio
async def test_create_sales_order_confirm_success():
    """Test create_sales_order with preview=False succeeds."""
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
            preview=False,
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
            preview=False,
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
        preview=True,
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
            preview=False,
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
            preview=False,
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
            preview=False,
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
            preview=True,
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
            preview=True,
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
            preview=True,
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
        preview=True,
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
        preview=False,
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
    """Build a mock SalesOrder attrs object for testing.

    Every SalesOrder attrs field is stubbed (mostly to UNSET) so
    ``unwrap_unset`` calls in the production impl don't leak raw MagicMock
    instances through Pydantic validation. Tests that need a populated
    field can assign it explicitly after the call.
    """
    so = MagicMock()
    so.id = id
    so.order_no = order_no
    so.customer_id = customer_id
    so.location_id = location_id
    so.status = status
    so.production_status = production_status
    so.invoicing_status = UNSET
    so.source = UNSET
    so.order_created_date = UNSET
    so.created_at = datetime(2026, 4, 10, 9, 0, tzinfo=UTC)
    so.updated_at = UNSET
    so.deleted_at = UNSET
    so.delivery_date = datetime(2026, 4, 20, 12, 0, tzinfo=UTC)
    so.picked_date = UNSET
    so.conversion_rate = UNSET
    so.conversion_date = UNSET
    so.total = total
    so.total_in_base_currency = UNSET
    so.currency = currency
    so.additional_info = UNSET
    so.customer_ref = UNSET
    so.product_availability = UNSET
    so.product_expected_date = UNSET
    so.ingredient_availability = UNSET
    so.ingredient_expected_date = UNSET
    so.tracking_number = UNSET
    so.tracking_number_url = UNSET
    so.billing_address_id = UNSET
    so.shipping_address_id = UNSET
    so.linked_manufacturing_order_id = UNSET
    so.shipping_fee = UNSET
    so.ecommerce_order_type = UNSET
    so.ecommerce_store_name = UNSET
    so.ecommerce_order_id = UNSET
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
    """Build a mock sales order row.

    Stubs every SalesOrderRow attrs field (mostly to UNSET) so the new
    exhaustive ``SalesOrderRowDetail`` mapping in ``_get_sales_order_impl``
    doesn't leak MagicMock instances through Pydantic validation.
    """
    r = MagicMock()
    r.id = id
    r.variant_id = variant_id
    r.quantity = quantity
    r.price_per_unit = price_per_unit
    r.linked_manufacturing_order_id = (
        linked_mo_id if linked_mo_id is not None else UNSET
    )
    r.sales_order_id = UNSET
    r.tax_rate_id = UNSET
    r.tax_rate = UNSET
    r.location_id = UNSET
    r.product_availability = UNSET
    r.product_expected_date = UNSET
    r.price_per_unit_in_base_currency = UNSET
    r.total = UNSET
    r.total_in_base_currency = UNSET
    r.total_discount = UNSET
    r.cogs_value = UNSET
    r.conversion_rate = UNSET
    r.conversion_date = UNSET
    r.serial_numbers = UNSET
    r.created_at = UNSET
    r.updated_at = UNSET
    r.deleted_at = UNSET
    return r


# ----------------------------------------------------------------------------
# Cache-seeding helpers (list_sales_orders reads from the SQLModel typed cache
# after #342). Tests pre-populate the cache with ``CachedSalesOrder`` rows,
# no-op the API-side sync via the ``no_sync`` fixture, and assert on the query
# results — mirroring how the live tool behaves in steady state (cache warm,
# sync returns zero rows).
# ----------------------------------------------------------------------------


@pytest.fixture
def no_sync():
    """Patch ``ensure_sales_orders_synced`` to a no-op for cache-backed tests.

    Uses the shared ``patch_typed_cache_sync`` helper from conftest so the
    same pattern applies to every entity's cache-backed tool tests.
    """
    with patch_typed_cache_sync("sales_orders"):
        yield


# ============================================================================
# list_sales_orders — filter predicates (translated from API kwargs to SQL
# WHERE clauses post-#342)
# ============================================================================


@pytest.mark.asyncio
async def test_list_sales_orders_passes_explicit_filters(
    context_with_typed_cache, no_sync
):
    """Explicit filters translate to SQL predicates that narrow the result set."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_sales_order(id=1, order_no="SO-100", customer_id=42),
            make_sales_order(id=2, order_no="SO-101", customer_id=43),
            make_sales_order(id=3, order_no="SO-102", customer_id=44),
        ],
    )

    result = await _list_sales_orders_impl(
        ListSalesOrdersRequest(customer_id=42), context
    )

    assert result.total_count == 1
    assert result.orders[0].customer_id == 42
    assert result.orders[0].order_no == "SO-100"


@pytest.mark.asyncio
async def test_list_sales_orders_zero_valued_filters_are_passed_through(
    context_with_typed_cache, no_sync
):
    """customer_id=0 is a valid predicate — must not be dropped as falsy."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_sales_order(id=1, customer_id=0),
            make_sales_order(id=2, customer_id=1),
        ],
    )

    result = await _list_sales_orders_impl(
        ListSalesOrdersRequest(customer_id=0), context
    )

    assert result.total_count == 1
    assert result.orders[0].id == 1
    assert result.orders[0].customer_id == 0


@pytest.mark.asyncio
async def test_list_sales_orders_needs_work_orders_shortcut(
    context_with_typed_cache, no_sync
):
    """needs_work_orders=True maps to production_status=NONE."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_sales_order(id=1, production_status="NONE"),
            make_sales_order(id=2, production_status="IN_PROGRESS"),
        ],
    )

    result = await _list_sales_orders_impl(
        ListSalesOrdersRequest(needs_work_orders=True), context
    )

    assert result.total_count == 1
    assert result.orders[0].id == 1
    assert result.orders[0].production_status == "NONE"


@pytest.mark.asyncio
async def test_list_sales_orders_explicit_production_status_wins_over_shortcut(
    context_with_typed_cache, no_sync
):
    """Explicit production_status overrides the needs_work_orders shortcut."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_sales_order(id=1, production_status="NONE"),
            make_sales_order(id=2, production_status="IN_PROGRESS"),
        ],
    )

    result = await _list_sales_orders_impl(
        ListSalesOrdersRequest(production_status="IN_PROGRESS", needs_work_orders=True),
        context,
    )

    assert result.total_count == 1
    assert result.orders[0].id == 2
    assert result.orders[0].production_status == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_list_sales_orders_server_side_date_filters_passed_through(
    context_with_typed_cache, no_sync
):
    """created_after / created_before bound the ``created_at`` range inclusively."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_sales_order(id=1, created_at=datetime(2025, 12, 15)),  # before window
            make_sales_order(id=2, created_at=datetime(2026, 2, 15)),  # inside
            make_sales_order(id=3, created_at=datetime(2026, 5, 1)),  # after window
        ],
    )

    result = await _list_sales_orders_impl(
        ListSalesOrdersRequest(
            created_after="2026-01-01T00:00:00+00:00",
            created_before="2026-04-01T00:00:00Z",
        ),
        context,
    )

    assert result.total_count == 1
    assert result.orders[0].id == 2


@pytest.mark.asyncio
async def test_list_sales_orders_ids_include_deleted_pass_through(
    context_with_typed_cache, no_sync
):
    """``include_deleted=True`` surfaces soft-deleted rows; default hides them."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_sales_order(id=1, deleted_at=None),
            make_sales_order(id=2, deleted_at=datetime(2026, 3, 15)),
        ],
    )

    # Default hides soft-deleted rows.
    default_result = await _list_sales_orders_impl(ListSalesOrdersRequest(), context)
    assert default_result.total_count == 1
    assert default_result.orders[0].id == 1

    # include_deleted=True surfaces them.
    with_deleted = await _list_sales_orders_impl(
        ListSalesOrdersRequest(include_deleted=True), context
    )
    assert with_deleted.total_count == 2


@pytest.mark.asyncio
async def test_list_sales_orders_delivered_filter_applied_server_side(
    context_with_typed_cache, no_sync
):
    """delivery_date range is now an indexed SQL predicate (post-#342).

    Renamed from ``..._client_side``: the pre-cache impl filtered these
    post-fetch; with the typed cache they're plain SQL WHERE clauses.
    """
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_sales_order(id=1, delivery_date=datetime(2026, 4, 20)),  # in window
            make_sales_order(id=2, delivery_date=datetime(2027, 1, 1)),  # outside
        ],
    )

    result = await _list_sales_orders_impl(
        ListSalesOrdersRequest(
            delivered_after="2026-04-01T00:00:00Z",
            delivered_before="2026-04-30T00:00:00Z",
        ),
        context,
    )

    assert result.total_count == 1
    assert result.orders[0].id == 1


# ============================================================================
# list_sales_orders — pagination + result shaping
# ============================================================================


@pytest.mark.asyncio
async def test_list_sales_orders_caps_results_to_request_limit(
    context_with_typed_cache, no_sync
):
    """``limit`` caps the result set at the SQL level (no over-fetch)."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [make_sales_order(id=i, order_no=f"SO-{i}") for i in range(1, 201)],
    )

    result = await _list_sales_orders_impl(ListSalesOrdersRequest(limit=50), context)

    assert len(result.orders) == 50
    assert result.total_count == 50


@pytest.mark.asyncio
async def test_list_sales_orders_returns_summary_rows(
    context_with_typed_cache, no_sync
):
    """Summaries carry id, order_no, total, and row_count from the cache."""
    context, _, typed_cache = context_with_typed_cache
    rows = [
        make_sales_order_row(id=1, sales_order_id=42, variant_id=100, quantity=2),
        make_sales_order_row(id=2, sales_order_id=42, variant_id=101, quantity=1),
    ]
    await seed_cache(
        typed_cache,
        [make_sales_order(id=42, order_no="SO-42", total=1234.56, rows=rows)],
    )

    result = await _list_sales_orders_impl(ListSalesOrdersRequest(), context)

    assert result.total_count == 1
    summary = result.orders[0]
    assert summary.id == 42
    assert summary.order_no == "SO-42"
    assert summary.total == 1234.56
    assert summary.row_count == 2


@pytest.mark.asyncio
async def test_list_sales_orders_page_populates_pagination_meta(
    context_with_typed_cache, no_sync
):
    """Explicit ``page`` populates PaginationMeta from a SQL COUNT(*)."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [make_sales_order(id=i, order_no=f"SO-{i}") for i in range(1, 31)],
    )

    result = await _list_sales_orders_impl(
        ListSalesOrdersRequest(page=2, limit=10), context
    )

    assert result.pagination is not None
    assert result.pagination.total_records == 30
    assert result.pagination.total_pages == 3
    assert result.pagination.page == 2
    assert result.pagination.first_page is False
    assert result.pagination.last_page is False
    assert len(result.orders) == 10


@pytest.mark.asyncio
async def test_list_sales_orders_no_page_leaves_pagination_none(
    context_with_typed_cache, no_sync
):
    """Without explicit ``page``, ``pagination`` stays None — the cache has
    no equivalent of a server-side ``x-pagination`` header to leak through."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(typed_cache, [make_sales_order(id=i) for i in range(1, 6)])

    result = await _list_sales_orders_impl(ListSalesOrdersRequest(), context)

    assert result.pagination is None
    assert result.total_count == 5


# ============================================================================
# list_sales_orders — validation
# ============================================================================


@pytest.mark.asyncio
async def test_list_sales_orders_invalid_server_date_raises(
    context_with_typed_cache, no_sync
):
    """Malformed ISO-8601 in a date filter surfaces as ValueError."""
    context, _, _ = context_with_typed_cache

    with pytest.raises(ValueError, match=r"Invalid ISO-8601.*created_after"):
        await _list_sales_orders_impl(
            ListSalesOrdersRequest(created_after="not-a-date"), context
        )


@pytest.mark.asyncio
async def test_list_sales_orders_limit_le_250_validation():
    """Request with limit > 250 is rejected at the schema boundary."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ListSalesOrdersRequest(limit=500)


@pytest.mark.asyncio
async def test_list_sales_orders_page_ge_1_validation():
    """page=0 is rejected at the schema boundary."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ListSalesOrdersRequest(page=0)


# ============================================================================
# list_sales_orders — include_rows (#332)
# ============================================================================


@pytest.mark.asyncio
async def test_list_sales_orders_include_rows_default_false_leaves_rows_none(
    context_with_typed_cache, no_sync
):
    """By default summaries carry rows=None (only row_count is populated)."""
    context, _, typed_cache = context_with_typed_cache
    rows = [
        make_sales_order_row(id=10, sales_order_id=1, variant_id=100, quantity=2),
        make_sales_order_row(id=11, sales_order_id=1, variant_id=101, quantity=1),
    ]
    await seed_cache(typed_cache, [make_sales_order(id=1, order_no="SO-1", rows=rows)])

    result = await _list_sales_orders_impl(ListSalesOrdersRequest(), context)

    assert result.total_count == 1
    assert result.orders[0].row_count == 2
    assert result.orders[0].rows is None


@pytest.mark.asyncio
async def test_list_sales_orders_include_rows_true_populates_rows(
    context_with_typed_cache, no_sync
):
    """include_rows=True surfaces per-row detail from sales_order_rows."""
    context, _, typed_cache = context_with_typed_cache
    rows = [
        make_sales_order_row(
            id=10,
            sales_order_id=42,
            variant_id=100,
            quantity=2,
            price_per_unit=50.0,
            linked_manufacturing_order_id=555,
        ),
        make_sales_order_row(
            id=11,
            sales_order_id=42,
            variant_id=101,
            quantity=1,
            price_per_unit=75.0,
        ),
    ]
    await seed_cache(
        typed_cache, [make_sales_order(id=42, order_no="SO-42", rows=rows)]
    )

    result = await _list_sales_orders_impl(
        ListSalesOrdersRequest(include_rows=True), context
    )

    summary = result.orders[0]
    assert summary.rows is not None
    assert len(summary.rows) == 2

    by_id = {r.id: r for r in summary.rows}
    assert by_id[10].variant_id == 100
    assert by_id[10].quantity == 2
    assert by_id[10].price_per_unit == 50.0
    assert by_id[10].linked_manufacturing_order_id == 555
    # sku is intentionally None in list context (get_sales_order enriches).
    assert by_id[10].sku is None

    assert by_id[11].variant_id == 101
    assert by_id[11].linked_manufacturing_order_id is None


@pytest.mark.asyncio
async def test_list_sales_orders_include_rows_handles_unset_fields(
    context_with_typed_cache, no_sync
):
    """Rows with None-valued optional fields serialize without crashing."""
    context, _, typed_cache = context_with_typed_cache
    sparse_row = make_sales_order_row(
        id=99,
        sales_order_id=1,
        variant_id=500,
        quantity=1.0,
        price_per_unit=None,
        linked_manufacturing_order_id=None,
    )
    await seed_cache(
        typed_cache, [make_sales_order(id=1, order_no="SO-1", rows=[sparse_row])]
    )

    result = await _list_sales_orders_impl(
        ListSalesOrdersRequest(include_rows=True), context
    )

    assert result.orders[0].rows is not None
    row = result.orders[0].rows[0]
    assert row.id == 99
    assert row.variant_id == 500
    assert row.price_per_unit is None
    assert row.linked_manufacturing_order_id is None
    assert row.sku is None


# ============================================================================
# get_sales_order tests
# ============================================================================


# Path of the internal helper that fetches /sales_order_addresses. Patched
# in tests so `_get_sales_order_impl` doesn't make a real HTTP call — SOs
# aren't cached today (per #342), so addresses are fetch-on-demand alongside
# the SO lookup.
_FETCH_ADDR_PATH = (
    "katana_mcp.tools.foundation.sales_orders._fetch_sales_order_addresses"
)


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
        patch(_FETCH_ADDR_PATH, AsyncMock(return_value=[])),
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
        patch(_FETCH_ADDR_PATH, AsyncMock(return_value=[])),
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
    """Row-level variant cache hits populate SalesOrderRowDetail.sku."""
    context, lifespan_ctx = create_mock_context()

    # Cache returns a variant dict for variant_id 500; missing IDs are
    # absent from the result (per get_many_by_ids contract).
    catalog = {500: {"id": 500, "sku": "BIKE-A", "display_name": "Bike A"}}

    async def fake_get_many_by_ids(_entity_type, variant_ids):
        return {vid: catalog[vid] for vid in variant_ids if vid in catalog}

    lifespan_ctx.cache.get_many_by_ids = AsyncMock(side_effect=fake_get_many_by_ids)

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
        patch(_FETCH_ADDR_PATH, AsyncMock(return_value=[])),
    ):
        result = await _get_sales_order_impl(GetSalesOrderRequest(order_id=9), context)

    assert result.rows[0].sku == "BIKE-A"  # cache hit
    assert result.rows[1].sku is None  # cache miss


# ============================================================================
# get_sales_order — exhaustive field coverage (#346)
# ============================================================================


def _make_mock_so_all_fields(*, so_id: int = 2001) -> MagicMock:
    """Build a mock SalesOrder attrs object with *every* field populated.

    Used by the full-coverage test so we can assert every previously-dropped
    field now surfaces on the response. Uses real enums where the attrs
    model stores an enum so `enum_to_str()` behaves like production.
    """
    from katana_public_api_client.models.ingredient_availability import (
        IngredientAvailability,
    )
    from katana_public_api_client.models.product_availability import (
        ProductAvailability,
    )
    from katana_public_api_client.models.sales_order_production_status import (
        SalesOrderProductionStatus,
    )

    so = MagicMock()
    so.id = so_id
    so.order_no = "SO-2024-001"
    so.customer_id = 1501
    so.location_id = 1
    so.status = SalesOrderStatus.NOT_SHIPPED
    so.source = "Shopify"
    so.order_created_date = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
    so.production_status = SalesOrderProductionStatus.IN_PROGRESS
    so.invoicing_status = "NOT_INVOICED"
    so.product_availability = ProductAvailability.IN_STOCK
    so.product_expected_date = datetime(2024, 1, 20, 0, 0, tzinfo=UTC)
    so.ingredient_availability = IngredientAvailability.IN_STOCK
    so.ingredient_expected_date = datetime(2024, 1, 18, 0, 0, tzinfo=UTC)
    so.delivery_date = datetime(2024, 1, 22, 14, 0, tzinfo=UTC)
    so.picked_date = datetime(2024, 1, 21, 9, 0, tzinfo=UTC)
    so.currency = "USD"
    so.total = 1250.0
    so.total_in_base_currency = 1250.0
    so.conversion_rate = 1.0
    so.conversion_date = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
    so.additional_info = "Customer requested expedited delivery"
    so.customer_ref = "CUST-REF-2024-001"
    so.tracking_number = "UPS1234567890"
    so.tracking_number_url = "https://www.ups.com/track?track=UPS1234567890"
    so.billing_address_id = 1201
    so.shipping_address_id = 1202
    so.linked_manufacturing_order_id = 7777
    so.ecommerce_order_type = "standard"
    so.ecommerce_store_name = "Kitchen Pro Store"
    so.ecommerce_order_id = "SHOP-5678-2024"
    so.created_at = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
    so.updated_at = datetime(2024, 1, 20, 16, 30, tzinfo=UTC)
    so.deleted_at = None

    # Nested shipping_fee with populated fields
    fee = MagicMock()
    fee.id = 2801
    fee.sales_order_id = so_id
    fee.amount = "25.99"
    fee.tax_rate_id = 301
    fee.description = "UPS Ground Shipping"
    so.shipping_fee = fee

    # One fully populated row so every SalesOrderRowDetail field has a value
    row = MagicMock()
    row.id = 2501
    row.variant_id = 2101
    row.quantity = 2.0
    row.sales_order_id = so_id
    row.tax_rate_id = 301
    row.tax_rate = 10.0
    row.location_id = 1
    row.product_availability = ProductAvailability.IN_STOCK
    row.product_expected_date = datetime(2024, 1, 20, 0, 0, tzinfo=UTC)
    row.price_per_unit = 599.99
    row.price_per_unit_in_base_currency = 599.99
    row.total = 1199.98
    row.total_in_base_currency = 1199.98
    row.total_discount = "0.00"
    row.cogs_value = 400.0
    row.linked_manufacturing_order_id = 7777
    row.conversion_rate = 1.0
    row.conversion_date = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
    row.serial_numbers = [10001, 10002]
    row.created_at = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
    row.updated_at = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
    row.deleted_at = None
    so.sales_order_rows = [row]

    return so


@pytest.mark.asyncio
async def test_get_sales_order_surfaces_every_sales_order_field():
    """get_sales_order exposes every field Katana puts on SalesOrder + rows.

    The pre-#346 response dropped ~20 SO-level fields (source, invoicing_status,
    product/ingredient availability, picked_date, total_in_base_currency,
    tracking, billing/shipping address IDs, ecommerce metadata, timestamps, etc.)
    and dropped most SalesOrderRow fields. This test pins the exhaustive
    coverage so a future refactor can't silently drop them again.
    """
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_id = AsyncMock(return_value=None)
    mock_so = _make_mock_so_all_fields(so_id=2001)

    with (
        patch(f"{_SO_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_SO_UNWRAP_AS, return_value=mock_so),
        patch(_FETCH_ADDR_PATH, AsyncMock(return_value=[])),
    ):
        result = await _get_sales_order_impl(
            GetSalesOrderRequest(order_id=2001), context
        )

    # Previously-dropped SO-level scalars:
    assert result.source == "Shopify"
    assert result.order_created_date == "2024-01-15T10:00:00+00:00"
    assert result.invoicing_status == "NOT_INVOICED"
    assert result.product_availability == "IN_STOCK"
    assert result.product_expected_date == "2024-01-20T00:00:00+00:00"
    assert result.ingredient_availability == "IN_STOCK"
    assert result.ingredient_expected_date == "2024-01-18T00:00:00+00:00"
    assert result.picked_date == "2024-01-21T09:00:00+00:00"
    assert result.total_in_base_currency == 1250.0
    assert result.conversion_rate == 1.0
    assert result.conversion_date == "2024-01-15T10:00:00+00:00"
    assert result.customer_ref == "CUST-REF-2024-001"
    assert result.tracking_number == "UPS1234567890"
    assert result.tracking_number_url == "https://www.ups.com/track?track=UPS1234567890"
    assert result.billing_address_id == 1201
    assert result.shipping_address_id == 1202
    assert result.linked_manufacturing_order_id == 7777
    assert result.ecommerce_order_type == "standard"
    assert result.ecommerce_store_name == "Kitchen Pro Store"
    assert result.ecommerce_order_id == "SHOP-5678-2024"
    assert result.created_at == "2024-01-15T10:00:00+00:00"
    assert result.updated_at == "2024-01-20T16:30:00+00:00"
    assert result.deleted_at is None

    # Nested shipping_fee surfaces with every field:
    assert result.shipping_fee is not None
    assert result.shipping_fee.id == 2801
    assert result.shipping_fee.amount == "25.99"
    assert result.shipping_fee.tax_rate_id == 301
    assert result.shipping_fee.description == "UPS Ground Shipping"

    # Per-row exhaustive detail — fields the pre-#346 SalesOrderRowInfo dropped:
    assert len(result.rows) == 1
    row = result.rows[0]
    assert row.id == 2501
    assert row.variant_id == 2101
    assert row.quantity == 2.0
    assert row.sales_order_id == 2001
    assert row.tax_rate_id == 301
    assert row.tax_rate == 10.0
    assert row.location_id == 1
    assert row.product_availability == "IN_STOCK"
    assert row.product_expected_date == "2024-01-20T00:00:00+00:00"
    assert row.price_per_unit == 599.99
    assert row.price_per_unit_in_base_currency == 599.99
    assert row.total == 1199.98
    assert row.total_in_base_currency == 1199.98
    assert row.total_discount == "0.00"
    assert row.cogs_value == 400.0
    assert row.linked_manufacturing_order_id == 7777
    assert row.conversion_rate == 1.0
    assert row.conversion_date == "2024-01-15T10:00:00+00:00"
    assert row.serial_numbers == [10001, 10002]
    assert row.created_at == "2024-01-15T10:00:00+00:00"
    assert row.updated_at == "2024-01-15T10:00:00+00:00"
    assert row.deleted_at is None


@pytest.mark.asyncio
async def test_get_sales_order_fetches_and_surfaces_addresses():
    """Addresses come from /sales_order_addresses, not the SO response.

    SOs aren't cached today (#342), so the tool fetches addresses on demand
    alongside the SO lookup. Patches the internal helper to assert the
    fetched results flow through to `response.addresses`.
    """
    from katana_mcp.tools.foundation.sales_orders import SalesOrderAddressInfo

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_id = AsyncMock(return_value=None)
    mock_so = _make_mock_so(id=2001, order_no="SO-2001")

    billing = SalesOrderAddressInfo(
        id=1201,
        sales_order_id=2001,
        entity_type="billing",
        first_name="Sarah",
        last_name="Johnson",
        company="Johnson's Restaurant",
        line_1="123 Main Street",
        city="Portland",
        state="OR",
        zip="97201",
        country="US",
    )
    shipping = SalesOrderAddressInfo(
        id=1202,
        sales_order_id=2001,
        entity_type="shipping",
        first_name="Sarah",
        last_name="Johnson",
        line_1="456 Oak Ave",
        city="Seattle",
        state="WA",
        zip="98101",
        country="US",
    )

    with (
        patch(f"{_SO_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_SO_UNWRAP_AS, return_value=mock_so),
        patch(_FETCH_ADDR_PATH, AsyncMock(return_value=[billing, shipping])),
    ):
        result = await _get_sales_order_impl(
            GetSalesOrderRequest(order_id=2001), context
        )

    assert len(result.addresses) == 2
    assert result.addresses[0].id == 1201
    assert result.addresses[0].entity_type == "billing"
    assert result.addresses[0].line_1 == "123 Main Street"
    # wire field name `zip` (not the attrs `zip_` workaround):
    assert result.addresses[0].zip == "97201"
    assert result.addresses[1].entity_type == "shipping"
    assert result.addresses[1].city == "Seattle"


@pytest.mark.asyncio
async def test_get_sales_order_markdown_uses_canonical_field_names():
    """Markdown labels use Pydantic field names (not prettified headers)
    so LLM consumers can't misread a section label as a different field.

    Pins the #346 canonical-name convention: scalar lines render as
    ``**field_name**: value``, empty lists render as ``**field_name**: []``,
    and non-empty lists render as ``**field_name** (N):`` with indented
    per-item blocks.
    """
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_id = AsyncMock(return_value=None)
    mock_so = _make_mock_so(
        id=2001,
        order_no="SO-2001",
        rows=[_make_mock_row(id=10, variant_id=500, quantity=1, price_per_unit=99.0)],
    )
    # Stamp distinctive values on fields whose labels we want to pin:
    mock_so.customer_ref = "CUST-REF-001"
    mock_so.tracking_number = "UPS1234567890"

    with (
        patch(f"{_SO_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_SO_UNWRAP_AS, return_value=mock_so),
        patch(_FETCH_ADDR_PATH, AsyncMock(return_value=[])),
    ):
        result = await get_sales_order(order_id=2001, context=context)

    text = result.content[0].text
    # Canonical-name scalar labels (not "Delivery", not "Tracking", etc.):
    assert "**delivery_date**:" in text
    assert "**customer_ref**: CUST-REF-001" in text
    assert "**tracking_number**: UPS1234567890" in text
    # Empty collections render with explicit [] so readers can't mistake
    # the heading for a section:
    assert "**addresses**: []" in text
    # Non-empty rows render with a count header:
    assert "**rows** (1):" in text


# ============================================================================
# format=json / format=markdown
# ============================================================================


def _content_text(result) -> str:
    """Extract the text of a ToolResult's first content block."""
    return result.content[0].text


@pytest.mark.asyncio
async def test_list_sales_orders_format_json_returns_json(
    context_with_typed_cache, no_sync
):
    """format='json' returns JSON-parseable content."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(typed_cache, [make_sales_order(id=1, order_no="SO-1")])

    result = await list_sales_orders(format="json", context=context)

    data = json.loads(_content_text(result))
    assert data["total_count"] == 1
    assert data["orders"][0]["order_no"] == "SO-1"


@pytest.mark.asyncio
async def test_list_sales_orders_format_markdown_default(
    context_with_typed_cache, no_sync
):
    """Default markdown format produces a table."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(typed_cache, [make_sales_order(id=1, order_no="SO-1")])

    result = await list_sales_orders(context=context)

    text = _content_text(result)
    assert "|" in text  # markdown table
    assert "SO-1" in text


@pytest.mark.asyncio
async def test_get_sales_order_format_json_returns_json():
    """format='json' returns JSON-parseable content."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_id = AsyncMock(return_value=None)
    mock_so = _make_mock_so(id=9, order_no="SO-9")

    with (
        patch(f"{_SO_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_SO_UNWRAP_AS, return_value=mock_so),
        patch(_FETCH_ADDR_PATH, AsyncMock(return_value=[])),
    ):
        result = await get_sales_order(order_id=9, format="json", context=context)

    data = json.loads(_content_text(result))
    assert data["id"] == 9
    assert data["order_no"] == "SO-9"


# ============================================================================
# modify_sales_order — unified modification surface
# ============================================================================


# Note: _SO_GET, _SO_UNWRAP_AS, _SO_UNWRAP_DATA are defined at top of file
# (around line 572). Adding only the constants the modify/delete tests need.
_MODIFY_SO_UPDATE = "katana_public_api_client.api.sales_order.update_sales_order"
_MODIFY_SO_DELETE = "katana_public_api_client.api.sales_order.delete_sales_order"
_MODIFY_SO_ROW_CREATE = (
    "katana_public_api_client.api.sales_order_row.create_sales_order_row"
)
# The modify/delete dispatcher pipes through ``_modification_dispatch.unwrap_as``.
_MODIFY_SO_UNWRAP_AS_LOCAL = "katana_mcp.tools._modification_dispatch.unwrap_as"


def _mock_so(order_id: int = 1, order_no: str = "SO-1"):
    """Build a mock SalesOrder attrs object with all fields defaulted to UNSET."""
    return mock_entity_for_modify(SalesOrder, id=order_id, order_no=order_no)


@pytest.mark.asyncio
async def test_modify_so_requires_at_least_one_subpayload():
    context, _ = create_mock_context()
    with pytest.raises(ValueError, match="At least one sub-payload"):
        await _modify_sales_order_impl(
            ModifySalesOrderRequest(id=42, preview=True), context
        )


@pytest.mark.asyncio
async def test_modify_so_preview_emits_planned_actions():
    """Preview returns one ActionResult per planned API call, all succeeded=None."""
    context, _ = create_mock_context()
    existing = _mock_so(order_id=42, order_no="SO-OLD")

    with patch(
        "katana_mcp.tools.foundation.sales_orders._fetch_sales_order_attrs",
        new_callable=AsyncMock,
        return_value=existing,
    ):
        request = ModifySalesOrderRequest(
            id=42,
            update_header=SOHeaderPatch(status="PACKED"),
            add_rows=[SORowAdd(variant_id=100, quantity=2)],
            preview=True,
        )
        response = await _modify_sales_order_impl(request, context)

    assert response.is_preview is True
    assert response.entity_id == 42
    assert len(response.actions) == 2
    assert response.actions[0].operation == "update_header"
    assert response.actions[1].operation == "add_row"
    assert all(a.succeeded is None for a in response.actions)


@pytest.mark.asyncio
async def test_modify_so_confirm_executes_in_canonical_order():
    """Header → row adds → row updates → row deletes → addresses → fulfillments → fees."""
    context, _ = create_mock_context()
    existing = _mock_so(order_id=42, order_no="SO-1")
    updated_so = _mock_so(order_id=42, order_no="SO-1")
    new_row = MagicMock()
    new_row.id = 555

    call_log: list[str] = []

    async def fake_update_so(*, id, client, body):
        call_log.append("PATCH /sales_orders/{id}")
        resp = MagicMock()
        resp.parsed = updated_so
        return resp

    async def fake_create_row(*, client, body):
        call_log.append("POST /sales_order_rows")
        resp = MagicMock()
        resp.parsed = new_row
        return resp

    with (
        patch(
            "katana_mcp.tools.foundation.sales_orders._fetch_sales_order_attrs",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch(f"{_MODIFY_SO_UPDATE}.asyncio_detailed", side_effect=fake_update_so),
        patch(f"{_MODIFY_SO_ROW_CREATE}.asyncio_detailed", side_effect=fake_create_row),
        patch(_MODIFY_SO_UNWRAP_AS_LOCAL, side_effect=[updated_so, new_row]),
    ):
        request = ModifySalesOrderRequest(
            id=42,
            update_header=SOHeaderPatch(status="PACKED"),
            add_rows=[SORowAdd(variant_id=100, quantity=2)],
            preview=False,
        )
        response = await _modify_sales_order_impl(request, context)

    assert response.is_preview is False
    assert all(a.succeeded is True for a in response.actions)
    assert call_log[0].startswith("PATCH")
    assert call_log[1].startswith("POST")
    assert response.prior_state is not None


@pytest.mark.asyncio
async def test_modify_so_address_update_marks_unknown_prior():
    """Address has no get-by-id endpoint, so update previews always show
    ``is_unknown_prior=True`` for the supplied fields."""
    context, _ = create_mock_context()
    existing = _mock_so(order_id=42, order_no="SO-1")

    with patch(
        "katana_mcp.tools.foundation.sales_orders._fetch_sales_order_attrs",
        new_callable=AsyncMock,
        return_value=existing,
    ):
        from katana_mcp.tools.foundation.sales_orders import SOAddressUpdate

        request = ModifySalesOrderRequest(
            id=42,
            update_addresses=[
                SOAddressUpdate(id=99, city="Springfield", zip="12345"),
            ],
            preview=True,
        )
        response = await _modify_sales_order_impl(request, context)

    assert response.is_preview is True
    assert len(response.actions) == 1
    assert response.actions[0].operation == "update_address"
    diffs = response.actions[0].changes
    assert all(c.is_unknown_prior for c in diffs)


@pytest.mark.asyncio
async def test_modify_so_fail_fast_halts_on_first_error():
    context, _ = create_mock_context()
    existing = _mock_so(order_id=42, order_no="SO-1")
    updated_so = _mock_so(order_id=42, order_no="SO-1")

    with (
        patch(
            "katana_mcp.tools.foundation.sales_orders._fetch_sales_order_attrs",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch(f"{_MODIFY_SO_UPDATE}.asyncio_detailed", new_callable=AsyncMock),
        patch(
            f"{_MODIFY_SO_ROW_CREATE}.asyncio_detailed",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ),
        patch(_MODIFY_SO_UNWRAP_AS_LOCAL, return_value=updated_so),
    ):
        request = ModifySalesOrderRequest(
            id=42,
            update_header=SOHeaderPatch(status="PACKED"),
            add_rows=[SORowAdd(variant_id=100, quantity=2)],
            preview=False,
        )
        response = await _modify_sales_order_impl(request, context)

    assert len(response.actions) == 2
    assert response.actions[0].succeeded is True
    assert response.actions[1].succeeded is False
    assert "boom" in (response.actions[1].error or "")


# ============================================================================
# delete_sales_order — destructive sibling
# ============================================================================


@pytest.mark.asyncio
async def test_delete_so_preview_returns_planned_action():
    context, _ = create_mock_context()
    existing = _mock_so(order_id=42, order_no="SO-1")

    with patch(
        "katana_mcp.tools.foundation.sales_orders._fetch_sales_order_attrs",
        new_callable=AsyncMock,
        return_value=existing,
    ):
        response = await _delete_sales_order_impl(
            DeleteSalesOrderRequest(id=42, preview=True), context
        )

    assert response.is_preview is True
    assert response.entity_id == 42
    assert len(response.actions) == 1
    assert response.actions[0].operation == "delete"
    assert response.actions[0].succeeded is None


@pytest.mark.asyncio
async def test_delete_so_confirm_calls_api_and_records_prior_state():
    context, _ = create_mock_context()
    existing = _mock_so(order_id=42, order_no="SO-1")
    api_response = MagicMock()
    api_response.status_code = 204

    with (
        patch(
            "katana_mcp.tools.foundation.sales_orders._fetch_sales_order_attrs",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch(
            f"{_MODIFY_SO_DELETE}.asyncio_detailed", new_callable=AsyncMock
        ) as mock_api,
        patch(
            "katana_mcp.tools._modification_dispatch.is_success",
            return_value=True,
        ),
    ):
        mock_api.return_value = api_response
        response = await _delete_sales_order_impl(
            DeleteSalesOrderRequest(id=42, preview=False), context
        )

    assert response.is_preview is False
    assert response.actions[0].succeeded is True
    assert response.prior_state is not None
    assert response.katana_url is None  # entity gone
    mock_api.assert_awaited_once()
