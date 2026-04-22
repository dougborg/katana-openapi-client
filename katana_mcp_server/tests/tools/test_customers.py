"""Tests for customer search and lookup tools."""

import json
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

from tests.conftest import create_mock_context


@pytest.fixture(autouse=True)
def _patch_cache_sync():
    """Patch customer sync for all unit tests.

    The @cache_read decorator caches sync functions in a module-level dict on
    first call, so patching the cache_sync module alone is not enough — we
    also need to clear and re-mock the cached mapping in the decorators module.
    """
    from katana_mcp.cache import EntityType
    from katana_mcp.tools import decorators

    mock_sync = AsyncMock()
    original = decorators._sync_fns
    decorators._sync_fns = {EntityType.CUSTOMER: mock_sync}
    try:
        with patch(
            "katana_mcp.cache_sync.ensure_customers_synced", new_callable=AsyncMock
        ):
            yield
    finally:
        decorators._sync_fns = original


# ============================================================================
# search_customers
# ============================================================================


@pytest.mark.asyncio
async def test_search_customers_returns_results():
    """Test search_customers with mocked cache."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.smart_search = AsyncMock(
        return_value=[
            {
                "id": 1,
                "name": "Acme Corp",
                "email": "billing@acme.com",
                "phone": "555-0100",
                "currency": "USD",
                "company": "Acme",
            },
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
    lifespan_ctx.cache.smart_search = AsyncMock(
        return_value=[{"id": 5, "name": "Minimal Customer"}]
    )

    request = SearchCustomersRequest(query="min")
    result = await _search_customers_impl(request, context)

    assert result.customers[0].id == 5
    assert result.customers[0].email is None
    assert result.customers[0].currency is None


# ============================================================================
# get_customer
# ============================================================================


@pytest.mark.asyncio
async def test_get_customer_by_id():
    """Test get_customer with mocked cache."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_id = AsyncMock(
        return_value={
            "id": 42,
            "name": "Widgets Inc",
            "email": "hello@widgets.io",
            "currency": "EUR",
            "category": "retail",
        }
    )

    request = GetCustomerRequest(customer_id=42)
    result = await _get_customer_impl(request, context)

    assert result.id == 42
    assert result.name == "Widgets Inc"
    assert result.email == "hello@widgets.io"
    assert result.currency == "EUR"
    assert result.category == "retail"


@pytest.mark.asyncio
async def test_get_customer_not_found():
    """Test get_customer raises when customer not found."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_id = AsyncMock(return_value=None)

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
    lifespan_ctx.cache.smart_search = AsyncMock(
        return_value=[{"id": 1, "name": "Acme Corp", "email": "a@b.c"}]
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
    lifespan_ctx.cache.smart_search = AsyncMock(
        return_value=[{"id": 1, "name": "Acme Corp", "email": "a@b.c"}]
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
    lifespan_ctx.cache.get_by_id = AsyncMock(
        return_value={"id": 42, "name": "Widgets Inc", "email": "hi@widgets.io"}
    )

    result = await get_customer(customer_id=42, format="json", context=context)

    data = json.loads(_content_text(result))
    assert data["id"] == 42
    assert data["name"] == "Widgets Inc"
