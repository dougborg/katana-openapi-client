"""Tests for customer search, lookup, and create tools."""

import json
from datetime import datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.customers import (
    CreateCustomerAddressRequest,
    CreateCustomerRequest,
    GetCustomerRequest,
    SearchCustomersRequest,
    _create_customer_impl,
    _customer_response_to_tool_result,
    _get_customer_impl,
    _search_customers_impl,
    get_customer,
    search_customers,
)
from katana_mcp_server.tests.conftest import create_mock_context

from katana_public_api_client.models import Customer as APICustomer
from katana_public_api_client.models_pydantic._generated import CachedCustomer
from tests.factories import mock_entity_for_modify


@pytest.fixture(autouse=True)
def _patch_cache_sync():
    """Patch the @cache_read sync registry to a no-op for all tests.

    The decorator memoizes its registry on first call; tests run before
    real wiring lands so we replace the registry with one that maps
    ``CachedCustomer`` to a no-op AsyncMock.
    """
    from katana_mcp.tools import decorators

    from katana_public_api_client.models_pydantic._generated import CachedCustomer

    mock_sync = AsyncMock()
    original = decorators._sync_fns
    decorators._sync_fns = {CachedCustomer: mock_sync}
    try:
        yield
    finally:
        decorators._sync_fns = original


def _make_cached_customer(**fields) -> CachedCustomer:
    """Build a ``CachedCustomer`` with sensible test defaults."""
    fields.setdefault("id", 1)
    fields.setdefault("name", "Test Customer")
    return CachedCustomer(**fields)


# ============================================================================
# search_customers
# ============================================================================


@pytest.mark.asyncio
async def test_search_customers_returns_results():
    """Test search_customers with mocked typed-cache catalog."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.smart_search = AsyncMock(
        return_value=[
            _make_cached_customer(
                id=1,
                name="Acme Corp",
                email="billing@acme.com",
                phone="555-0100",
                currency="USD",
                company="Acme",
            ),
        ]
    )

    request = SearchCustomersRequest(query="acme", limit=20)
    result = await _search_customers_impl(request, context)

    assert result.total_count == 1
    assert result.customers[0].name == "Acme Corp"
    assert result.customers[0].email == "billing@acme.com"


@pytest.mark.asyncio
async def test_search_customers_empty_query():
    """Test search_customers rejects empty query."""
    context, _ = create_mock_context()

    request = SearchCustomersRequest(query="")
    with pytest.raises(ValueError, match="cannot be empty"):
        await _search_customers_impl(request, context)


@pytest.mark.asyncio
async def test_search_customers_whitespace_query():
    """Test search_customers rejects whitespace-only query."""
    context, _ = create_mock_context()

    request = SearchCustomersRequest(query="   ")
    with pytest.raises(ValueError, match="cannot be empty"):
        await _search_customers_impl(request, context)


@pytest.mark.asyncio
async def test_search_customers_zero_limit():
    """Test search_customers rejects zero limit."""
    context, _ = create_mock_context()

    request = SearchCustomersRequest(query="test", limit=0)
    with pytest.raises(ValueError, match="Limit must be positive"):
        await _search_customers_impl(request, context)


@pytest.mark.asyncio
async def test_search_customers_handles_missing_fields():
    """Test that optional fields default gracefully."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.smart_search = AsyncMock(
        return_value=[_make_cached_customer(id=5, name="Minimal Customer")]
    )

    request = SearchCustomersRequest(query="min")
    result = await _search_customers_impl(request, context)

    assert result.customers[0].id == 5
    assert result.customers[0].email is None
    assert result.customers[0].currency is None


# ============================================================================
# get_customer
# ============================================================================


_FETCH_ADDR_PATH = "katana_mcp.tools.foundation.customers._fetch_customer_addresses"


@pytest.mark.asyncio
async def test_get_customer_by_id():
    """get_customer returns every Customer field the cache row carries."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(
        return_value=_make_cached_customer(
            id=42,
            name="Widgets Inc",
            first_name="Sarah",
            last_name="Johnson",
            email="hello@widgets.io",
            phone="+1-555-0123",
            company="Widgets Inc",
            currency="EUR",
            reference_id="WGT-2024-001",
            category="retail",
            discount_rate=5.0,
            default_billing_id=3001,
            default_shipping_id=3002,
            comment="High-volume",
            created_at=datetime(2024, 1, 10, 9, 0, 0),
            updated_at=datetime(2024, 1, 15, 14, 30, 0),
            deleted_at=None,
        )
    )

    request = GetCustomerRequest(customer_id=42)
    with patch(_FETCH_ADDR_PATH, AsyncMock(return_value=[])):
        result = await _get_customer_impl(request, context)

    assert result.id == 42
    assert result.name == "Widgets Inc"
    assert result.first_name == "Sarah"
    assert result.last_name == "Johnson"
    assert result.phone == "+1-555-0123"
    assert result.reference_id == "WGT-2024-001"
    assert result.discount_rate == 5.0
    assert result.default_billing_id == 3001
    assert result.default_shipping_id == 3002
    assert result.created_at == "2024-01-10T09:00:00"
    assert result.updated_at == "2024-01-15T14:30:00"
    # Fields that were already there stay correct:
    assert result.email == "hello@widgets.io"
    assert result.currency == "EUR"
    assert result.category == "retail"
    # Addresses default to empty list when none are registered:
    assert result.addresses == []


@pytest.mark.asyncio
async def test_get_customer_fetches_and_surfaces_addresses():
    """Addresses come from the customer_addresses endpoint, not the cache."""
    from katana_mcp.tools.foundation.customers import CustomerAddressInfo

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(
        return_value=_make_cached_customer(id=42, name="Widgets Inc")
    )
    address = CustomerAddressInfo(
        id=3001,
        customer_id=42,
        entity_type="billing",
        default=True,
        first_name="Sarah",
        line_1="123 Main St",
        city="Chicago",
        state="IL",
        zip="60601",
        country="US",
    )

    request = GetCustomerRequest(customer_id=42)
    with patch(_FETCH_ADDR_PATH, AsyncMock(return_value=[address])):
        result = await _get_customer_impl(request, context)

    assert len(result.addresses) == 1
    assert result.addresses[0].id == 3001
    assert result.addresses[0].line_1 == "123 Main St"
    assert result.addresses[0].entity_type == "billing"


@pytest.mark.asyncio
async def test_get_customer_uses_canonical_field_names_in_content():
    """Response content uses Pydantic field names (not prettified headers)
    so LLM consumers can't misread a key as a different field — same
    motivation as the #346 supplier_item_codes misread, now satisfied by
    JSON content keying off the Pydantic field names directly."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(
        return_value=_make_cached_customer(
            id=42,
            name="Widgets Inc",
            reference_id="WGT-2024-001",
            discount_rate=5.0,
        )
    )

    with patch(_FETCH_ADDR_PATH, AsyncMock(return_value=[])):
        result = await get_customer(customer_id=42, context=context)

    data = json.loads(result.content[0].text)
    # Field names appear as JSON keys (not prettified headers).
    assert data["reference_id"] == "WGT-2024-001"
    assert data["discount_rate"] == 5.0
    # Empty address list serializes as the empty array, not a section header.
    assert data["addresses"] == []


@pytest.mark.asyncio
async def test_get_customer_not_found():
    """Test get_customer raises when customer not found."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(return_value=None)

    request = GetCustomerRequest(customer_id=9999)
    with pytest.raises(ValueError, match="Customer with ID 9999 not found"):
        await _get_customer_impl(request, context)


# ============================================================================
# JSON content (#567 — markdown formatters dropped, JSON is the only mode)
# ============================================================================


def _content_text(result) -> str:
    """Extract the text of a ToolResult's first content block."""
    return result.content[0].text


@pytest.mark.asyncio
async def test_search_customers_content_is_indented_json():
    """``content`` is the indented JSON form of the response model.
    Programmatic consumers can ``json.loads`` it and get the same shape
    as ``structured_content``."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.smart_search = AsyncMock(
        return_value=[_make_cached_customer(id=1, name="Acme Corp", email="a@b.c")]
    )

    result = await search_customers(query="acme", limit=20, context=context)

    data = json.loads(_content_text(result))
    assert data["total_count"] == 1
    assert data["customers"][0]["name"] == "Acme Corp"
    # Structured content carries the same payload (per the #567 contract).
    assert result.structured_content["total_count"] == 1


@pytest.mark.asyncio
async def test_get_customer_content_is_indented_json():
    """get_customer ``content`` parses as JSON matching the response shape."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(
        return_value=_make_cached_customer(
            id=42, name="Widgets Inc", email="hi@widgets.io"
        )
    )

    with patch(_FETCH_ADDR_PATH, AsyncMock(return_value=[])):
        result = await get_customer(customer_id=42, context=context)

    data = json.loads(_content_text(result))
    assert data["id"] == 42
    assert data["name"] == "Widgets Inc"


# ============================================================================
# create_customer
# ============================================================================


_MERGE_CACHE_PATH = "katana_mcp.typed_cache.sync.merge_filtered_fetch"


@pytest.mark.asyncio
async def test_create_customer_preview_skips_api_call():
    """Preview branch must echo request fields without hitting the API or cache."""
    context, _ = create_mock_context()

    request = CreateCustomerRequest(
        name="Acme Corp",
        company="Acme Corp",
        email="orders@acme.com",
        phone="+1-555-0100",
        currency="USD",
        category="Wholesale",
        discount_rate=7.5,
        preview=True,
    )

    # ``merge_filtered_fetch`` should NOT be called on the preview branch —
    # patch it so the test fails loudly if the impl regresses.
    with patch(_MERGE_CACHE_PATH, AsyncMock()) as merge_mock:
        result = await _create_customer_impl(request, context)

    assert result.is_preview is True
    assert result.id is None
    assert result.katana_url is None
    assert result.name == "Acme Corp"
    assert result.company == "Acme Corp"
    assert result.email == "orders@acme.com"
    assert result.currency == "USD"
    assert result.discount_rate == 7.5
    assert result.addresses == []
    assert "preview=false" in result.message.lower() or result.message.startswith(
        "Preview"
    )
    merge_mock.assert_not_called()


@pytest.mark.asyncio
async def test_create_customer_preview_carries_addresses():
    """Addresses on the request flow through to the preview response snapshot."""
    context, _ = create_mock_context()

    billing = CreateCustomerAddressRequest(
        entity_type="billing",
        first_name="Elena",
        last_name="Rodriguez",
        line_1="123 Market St",
        city="Springfield",
        state="IL",
        zip="62701",
        country="US",
    )
    shipping = CreateCustomerAddressRequest(
        entity_type="shipping",
        first_name="Elena",
        last_name="Rodriguez",
        line_1="500 Warehouse Way",
        city="Springfield",
        state="IL",
        zip="62702",
        country="US",
    )
    request = CreateCustomerRequest(
        name="Gourmet Bistro Group",
        addresses=[billing, shipping],
        preview=True,
    )

    result = await _create_customer_impl(request, context)

    assert result.is_preview is True
    assert len(result.addresses) == 2
    assert result.addresses[0].entity_type == "billing"
    assert result.addresses[0].line_1 == "123 Market St"
    assert result.addresses[1].entity_type == "shipping"
    assert result.addresses[1].line_1 == "500 Warehouse Way"


@pytest.mark.asyncio
async def test_create_customer_empty_name_rejected():
    """Empty or whitespace-only ``name`` raises before any API call."""
    context, _ = create_mock_context()

    request = CreateCustomerRequest(name="   ", preview=True)
    with pytest.raises(ValueError, match="name cannot be empty"):
        await _create_customer_impl(request, context)


def test_create_customer_discount_rate_out_of_range_rejected():
    """``discount_rate`` outside 0-100 raises at request-parse time —
    a clean ValidationError rather than an opaque Katana 422 on apply.
    """
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="less than or equal to 100"):
        CreateCustomerRequest(name="X", discount_rate=150)
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        CreateCustomerRequest(name="X", discount_rate=-1)


@pytest.mark.asyncio
async def test_create_customer_apply_calls_api_and_merges_cache():
    """Apply branch must POST to /customers and write through to the cache."""
    context, _ = create_mock_context()

    api_customer = mock_entity_for_modify(
        APICustomer,
        id=8001,
        name="Acme Corp",
        email="orders@acme.com",
        currency="USD",
        category="Wholesale",
    )
    mock_api_response = MagicMock()
    mock_api_response.status_code = 200
    mock_api_response.parsed = api_customer
    mock_api_call = AsyncMock(return_value=mock_api_response)

    import katana_public_api_client.api.customer.create_customer as create_module

    original = create_module.asyncio_detailed
    cast(Any, create_module).asyncio_detailed = mock_api_call

    try:
        with patch(_MERGE_CACHE_PATH, AsyncMock()) as merge_mock:
            request = CreateCustomerRequest(
                name="Acme Corp",
                email="orders@acme.com",
                currency="USD",
                category="Wholesale",
                preview=False,
            )
            result = await _create_customer_impl(request, context)
    finally:
        create_module.asyncio_detailed = original

    assert result.is_preview is False
    assert result.id == 8001
    assert result.name == "Acme Corp"
    assert result.email == "orders@acme.com"
    assert result.currency == "USD"
    assert result.katana_url is not None
    assert "8001" in result.katana_url
    # Cache write-through must have been invoked with the fresh attrs object.
    merge_mock.assert_called_once()
    args, _kwargs = merge_mock.call_args
    # merge_filtered_fetch(cache, spec, [attrs_obj])
    assert args[2] == [api_customer]
    # And the API was called exactly once with the right body shape.
    mock_api_call.assert_called_once()
    body = mock_api_call.call_args.kwargs["body"]
    assert body.name == "Acme Corp"
    assert body.email == "orders@acme.com"
    assert body.currency == "USD"


@pytest.mark.asyncio
async def test_create_customer_apply_forwards_addresses_to_api():
    """Addresses on the request must reach the API attrs body verbatim."""
    context, _ = create_mock_context()

    api_customer = mock_entity_for_modify(APICustomer, id=8002, name="Bistro Group")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = api_customer
    mock_api_call = AsyncMock(return_value=mock_response)

    import katana_public_api_client.api.customer.create_customer as create_module

    original = create_module.asyncio_detailed
    cast(Any, create_module).asyncio_detailed = mock_api_call
    try:
        with patch(_MERGE_CACHE_PATH, AsyncMock()):
            request = CreateCustomerRequest(
                name="Bistro Group",
                addresses=[
                    CreateCustomerAddressRequest(
                        entity_type="billing",
                        line_1="123 Market St",
                        city="Springfield",
                        zip="62701",
                        country="US",
                    )
                ],
                preview=False,
            )
            await _create_customer_impl(request, context)
    finally:
        create_module.asyncio_detailed = original

    body = mock_api_call.call_args.kwargs["body"]
    assert len(body.addresses) == 1
    addr = body.addresses[0]
    # AddressEntityType is an enum on the attrs side; ``.value`` is "billing".
    assert addr.entity_type.value == "billing"
    assert addr.line_1 == "123 Market St"
    # zip → zip_ wire-name workaround on the attrs model.
    assert addr.zip_ == "62701"


@pytest.mark.asyncio
async def test_create_customer_apply_prefers_server_addresses_over_request_snapshot():
    """When the API echoes addresses on the create response (with
    server-assigned ``id`` / ``default`` + normalized values), the tool
    surfaces those — not the request snapshot — so the card reflects what
    Katana actually stored.
    """
    from katana_public_api_client.client_types import UNSET
    from katana_public_api_client.models import (
        AddressEntityType,
        CustomerAddress,
    )

    context, _ = create_mock_context()

    # Real attrs CustomerAddress: ``zip_`` (Python keyword workaround) +
    # AddressEntityType enum for entity_type. Katana normalized country
    # 'USA' → 'US' and assigned id=3001 / default=True.
    server_billing = CustomerAddress(
        id=3001,
        customer_id=8020,
        entity_type=AddressEntityType.BILLING,
        default=True,
        first_name="Elena",
        line_1="123 Market St",
        city="Springfield",
        state="IL",
        zip_="62701",
        country="US",
        created_at=UNSET,
        updated_at=UNSET,
        deleted_at=UNSET,
    )
    api_customer = mock_entity_for_modify(
        APICustomer,
        id=8020,
        name="Server Address Echo Co",
        addresses=[server_billing],
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = api_customer

    import katana_public_api_client.api.customer.create_customer as create_module

    original = create_module.asyncio_detailed
    cast(Any, create_module).asyncio_detailed = AsyncMock(return_value=mock_response)
    try:
        with patch(_MERGE_CACHE_PATH, AsyncMock()):
            # Request submitted with country='USA' (un-normalized) — should
            # be replaced by the server's 'US' in the response.
            request = CreateCustomerRequest(
                name="Server Address Echo Co",
                addresses=[
                    CreateCustomerAddressRequest(
                        entity_type="billing",
                        first_name="Elena",
                        line_1="123 Market St",
                        city="Springfield",
                        state="IL",
                        zip="62701",
                        country="USA",
                    )
                ],
                preview=False,
            )
            result = await _create_customer_impl(request, context)
    finally:
        create_module.asyncio_detailed = original

    assert len(result.addresses) == 1
    addr = result.addresses[0]
    assert addr.id == 3001  # server-assigned
    assert addr.default is True  # server-assigned
    assert addr.country == "US"  # server-normalized (not request 'USA')
    assert addr.entity_type == "billing"


@pytest.mark.asyncio
async def test_create_customer_apply_surfaces_warning_when_cache_merge_fails():
    """Cache-merge failure must NOT raise — the customer already exists in
    Katana, so re-raising would push the operator into retrying and creating
    a duplicate. The tool returns is_preview=False with a warning instead.
    """
    context, _ = create_mock_context()

    api_customer = mock_entity_for_modify(APICustomer, id=8010, name="Cache Failure Co")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = api_customer

    import katana_public_api_client.api.customer.create_customer as create_module

    original = create_module.asyncio_detailed
    cast(Any, create_module).asyncio_detailed = AsyncMock(return_value=mock_response)
    try:
        with patch(
            _MERGE_CACHE_PATH,
            AsyncMock(side_effect=RuntimeError("database is locked")),
        ):
            request = CreateCustomerRequest(name="Cache Failure Co", preview=False)
            result = await _create_customer_impl(request, context)
    finally:
        create_module.asyncio_detailed = original

    # Customer was created in Katana; we don't lose that fact just because
    # the cache write-through failed.
    assert result.is_preview is False
    assert result.id == 8010
    # Warning surfaces what happened + explicit "do not retry" coaching.
    assert any("cache" in w.lower() for w in result.warnings)
    assert any("duplicate" in w.lower() for w in result.warnings)


@pytest.mark.asyncio
async def test_create_customer_apply_writes_through_to_real_cache(typed_cache_engine):
    """Integration: apply branch writes a row that ``search_customers`` can
    immediately read back via the real typed cache — no ``rebuild_cache``
    round-trip needed (the cache-merge contract on #817).
    """
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache = typed_cache_engine

    # Real APICustomer (not MagicMock) — the cache converter calls
    # ``Customer.from_attrs(attrs_obj)`` which validates field shapes.
    api_customer = APICustomer(
        id=8003,
        name="Cache Writethrough Test Co",
        email="qa@example.com",
        currency="USD",
    )
    mock_api_response = MagicMock()
    mock_api_response.status_code = 200
    mock_api_response.parsed = api_customer

    import katana_public_api_client.api.customer.create_customer as create_module

    original = create_module.asyncio_detailed
    cast(Any, create_module).asyncio_detailed = AsyncMock(
        return_value=mock_api_response
    )
    try:
        request = CreateCustomerRequest(
            name="Cache Writethrough Test Co",
            email="qa@example.com",
            currency="USD",
            preview=False,
        )
        await _create_customer_impl(request, context)
    finally:
        create_module.asyncio_detailed = original

    # search_customers reads through the cache via smart_search. Query the
    # catalog directly — it's the same data path search_customers uses.
    rows = await typed_cache_engine.catalog.smart_search(
        CachedCustomer, "Cache Writethrough", limit=10
    )
    assert any(r.id == 8003 for r in rows)


def test_create_customer_response_to_tool_result_emits_prefab_card():
    """The ToolResult must carry the Prefab card envelope, not plain JSON."""
    from katana_mcp.tools.foundation.customers import CreateCustomerResponse

    response = CreateCustomerResponse(
        name="Acme Corp",
        is_preview=True,
        message="Preview",
    )
    request = CreateCustomerRequest(name="Acme Corp", preview=True)

    result = _customer_response_to_tool_result(response, request=request)

    # structured_content is the Prefab wire envelope — fastmcp serializes
    # the PrefabApp into a ``$prefab`` / ``state`` / ``view`` dict at
    # ToolResult construction time.
    assert isinstance(result.structured_content, dict)
    assert "$prefab" in result.structured_content
    assert "view" in result.structured_content
    # content channel carries the response JSON for the model context.
    data = json.loads(_content_text(result))
    assert data["name"] == "Acme Corp"
    assert data["is_preview"] is True
