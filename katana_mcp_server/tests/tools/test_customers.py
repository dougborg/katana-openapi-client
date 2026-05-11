"""Tests for customer search and lookup tools."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from katana_mcp.tools.foundation.customers import (
    GetCustomerRequest,
    SearchCustomersRequest,
    _get_customer_impl,
    _search_customers_impl,
    get_customer,
    search_customers,
)
from katana_mcp_server.tests.conftest import create_mock_context

from katana_public_api_client.models_pydantic._generated import CachedCustomer


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
async def test_get_customer_markdown_uses_canonical_field_names():
    """Markdown labels use Pydantic field names (not prettified headers)
    so LLM consumers can't misread a section label as a different field
    (motivation: #346 follow-on, supplier_item_codes misread)."""
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

    text = result.content[0].text
    assert "**reference_id**: WGT-2024-001" in text
    assert "**discount_rate**: 5.0" in text
    # Empty address list renders with explicit [] syntax, not a heading
    # that a reader might mistake for a section:
    assert "**addresses**: []" in text


@pytest.mark.asyncio
async def test_get_customer_not_found():
    """Test get_customer raises when customer not found."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(return_value=None)

    request = GetCustomerRequest(customer_id=9999)
    with pytest.raises(ValueError, match="Customer with ID 9999 not found"):
        await _get_customer_impl(request, context)


# ============================================================================
# format=json / format=markdown
# ============================================================================


def _content_text(result) -> str:
    """Extract the text of a ToolResult's first content block."""
    return result.content[0].text


@pytest.mark.asyncio
async def test_search_customers_format_json_returns_json():
    """format='json' returns JSON-parseable content."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.smart_search = AsyncMock(
        return_value=[_make_cached_customer(id=1, name="Acme Corp", email="a@b.c")]
    )

    result = await search_customers(
        query="acme", limit=20, format="json", context=context
    )

    data = json.loads(_content_text(result))
    assert data["total_count"] == 1
    assert data["customers"][0]["name"] == "Acme Corp"


@pytest.mark.asyncio
async def test_search_customers_format_markdown_default():
    """Default markdown format produces markdown-ish content (not JSON)."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.smart_search = AsyncMock(
        return_value=[_make_cached_customer(id=1, name="Acme Corp", email="a@b.c")]
    )

    result = await search_customers(query="acme", limit=20, context=context)

    text = _content_text(result)
    assert "Acme Corp" in text
    # Not JSON — should have markdown characters
    assert "##" in text or "**" in text


@pytest.mark.asyncio
async def test_get_customer_format_json_returns_json():
    """format='json' returns JSON-parseable content."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(
        return_value=_make_cached_customer(
            id=42, name="Widgets Inc", email="hi@widgets.io"
        )
    )

    with patch(_FETCH_ADDR_PATH, AsyncMock(return_value=[])):
        result = await get_customer(customer_id=42, format="json", context=context)

    data = json.loads(_content_text(result))
    assert data["id"] == 42
    assert data["name"] == "Widgets Inc"
