"""Tests for reference data resources (suppliers, locations, tax-rates, operators)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.resources.reference import (
    get_locations,
    get_operators,
    get_suppliers,
    get_tax_rates,
    register_resources,
)

from tests.conftest import create_mock_context


def _make_context_with_cache(cached_entities: list[dict]):
    """Create a mock context with pre-populated cache data."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_all = AsyncMock(return_value=cached_entities)
    return context


async def _call_and_parse(handler, context) -> dict:
    """Call a resource handler and parse its JSON string response."""
    result = await handler(context)
    assert isinstance(result, str), "Resource handlers must return JSON strings"
    return json.loads(result)


# ============================================================================
# Suppliers resource
# ============================================================================


class TestSuppliersResource:
    @pytest.mark.asyncio
    async def test_returns_expected_shape(self):
        context = _make_context_with_cache(
            [
                {
                    "id": 1,
                    "name": "Acme Corp",
                    "email": "sales@acme.com",
                    "phone": "555-0100",
                    "currency": "USD",
                    "comment": None,
                },
            ]
        )
        with patch(
            "katana_mcp.resources.reference.ensure_suppliers_synced",
            new_callable=AsyncMock,
        ):
            result = await _call_and_parse(get_suppliers, context)

        assert "generated_at" in result
        assert result["summary"]["total_suppliers"] == 1
        assert len(result["suppliers"]) == 1
        assert result["suppliers"][0]["id"] == 1
        assert result["suppliers"][0]["name"] == "Acme Corp"
        assert result["next_actions"]

    @pytest.mark.asyncio
    async def test_filters_deleted(self):
        context = _make_context_with_cache(
            [
                {"id": 1, "name": "Active", "deleted_at": None},
                {"id": 2, "name": "Deleted", "deleted_at": "2026-01-01T00:00:00Z"},
            ]
        )
        with patch(
            "katana_mcp.resources.reference.ensure_suppliers_synced",
            new_callable=AsyncMock,
        ):
            result = await _call_and_parse(get_suppliers, context)

        assert result["summary"]["total_suppliers"] == 1
        assert result["suppliers"][0]["id"] == 1

    @pytest.mark.asyncio
    async def test_empty_cache(self):
        context = _make_context_with_cache([])
        with patch(
            "katana_mcp.resources.reference.ensure_suppliers_synced",
            new_callable=AsyncMock,
        ):
            result = await _call_and_parse(get_suppliers, context)

        assert result["summary"]["total_suppliers"] == 0
        assert result["suppliers"] == []

    @pytest.mark.asyncio
    async def test_calls_ensure_synced_before_get_all(self):
        context = _make_context_with_cache([])
        with patch(
            "katana_mcp.resources.reference.ensure_suppliers_synced",
            new_callable=AsyncMock,
        ) as mock_sync:
            await get_suppliers(context)
            mock_sync.assert_awaited_once()


# ============================================================================
# Locations resource
# ============================================================================


class TestLocationsResource:
    @pytest.mark.asyncio
    async def test_returns_expected_shape(self):
        context = _make_context_with_cache(
            [
                {
                    "id": 100,
                    "name": "Main Warehouse",
                    "address": "123 Industrial Way",
                    "city": "Portland",
                    "country": "US",
                    "is_primary": True,
                },
            ]
        )
        with patch(
            "katana_mcp.resources.reference.ensure_locations_synced",
            new_callable=AsyncMock,
        ):
            result = await _call_and_parse(get_locations, context)

        assert result["summary"]["total_locations"] == 1
        assert result["locations"][0]["name"] == "Main Warehouse"
        assert result["locations"][0]["is_primary"] is True

    @pytest.mark.asyncio
    async def test_filters_deleted(self):
        context = _make_context_with_cache(
            [
                {"id": 1, "name": "Active"},
                {"id": 2, "name": "Closed", "deleted_at": "2026-01-01T00:00:00Z"},
            ]
        )
        with patch(
            "katana_mcp.resources.reference.ensure_locations_synced",
            new_callable=AsyncMock,
        ):
            result = await _call_and_parse(get_locations, context)

        assert result["summary"]["total_locations"] == 1


# ============================================================================
# Tax Rates resource
# ============================================================================


class TestTaxRatesResource:
    @pytest.mark.asyncio
    async def test_returns_expected_shape(self):
        context = _make_context_with_cache(
            [
                {
                    "id": 1,
                    "name": "Standard",
                    "rate": 8.5,
                    "display_name": "CA Sales Tax",
                    "is_default_sales": True,
                    "is_default_purchases": False,
                },
            ]
        )
        with patch(
            "katana_mcp.resources.reference.ensure_tax_rates_synced",
            new_callable=AsyncMock,
        ):
            result = await _call_and_parse(get_tax_rates, context)

        assert result["summary"]["total_tax_rates"] == 1
        assert result["tax_rates"][0]["rate"] == 8.5
        assert result["tax_rates"][0]["is_default_sales"] is True


# ============================================================================
# Operators resource
# ============================================================================


class TestOperatorsResource:
    @pytest.mark.asyncio
    async def test_returns_expected_shape(self):
        context = _make_context_with_cache(
            [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
        )
        with patch(
            "katana_mcp.resources.reference.ensure_operators_synced",
            new_callable=AsyncMock,
        ):
            result = await _call_and_parse(get_operators, context)

        assert result["summary"]["total_operators"] == 2
        assert {op["name"] for op in result["operators"]} == {"Alice", "Bob"}


# ============================================================================
# Registration
# ============================================================================


class TestRegistration:
    def test_registers_four_resources(self):
        mcp = MagicMock()
        resource_decorator = MagicMock(return_value=lambda fn: fn)
        mcp.resource = MagicMock(return_value=resource_decorator)

        register_resources(mcp)

        # Four resource decorators should have been created
        assert mcp.resource.call_count == 4
        uris = [call.kwargs["uri"] for call in mcp.resource.call_args_list]
        assert "katana://suppliers" in uris
        assert "katana://locations" in uris
        assert "katana://tax-rates" in uris
        assert "katana://operators" in uris

    def test_order_resources_not_registered(self):
        """Verify no order resources are registered by the reference module."""
        mcp = MagicMock()
        resource_decorator = MagicMock(return_value=lambda fn: fn)
        mcp.resource = MagicMock(return_value=resource_decorator)

        register_resources(mcp)

        uris = [call.kwargs["uri"] for call in mcp.resource.call_args_list]
        for removed in (
            "katana://sales-orders",
            "katana://purchase-orders",
            "katana://manufacturing-orders",
            "katana://inventory/stock-movements",
        ):
            assert removed not in uris
