"""Tests for parameterized reference-data tools."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp.tools import ToolResult
from katana_mcp.cache import EntityType
from katana_mcp.tools import decorators
from katana_mcp.tools.foundation.reference import (
    GetSupplierRequest,
    ListAdditionalCostsRequest,
    ListLocationsRequest,
    ListOperatorsRequest,
    ListSuppliersRequest,
    ListTaxRatesRequest,
    get_supplier,
    list_additional_costs,
    list_locations,
    list_operators,
    list_suppliers,
    list_tax_rates,
    register_tools,
)
from katana_mcp_server.tests.conftest import create_mock_context
from mcp.types import TextContent


@pytest.fixture(autouse=True)
def _patch_cache_sync():
    """Stub @cache_read sync fns so cache reads don't trigger API fetches."""
    # Direct dict replacement (not patch.dict): the decorator caches its
    # entity_type → sync_fn map by reference on first call, so patching
    # `katana_mcp.cache_sync` after the dict is populated has no effect.
    original = decorators._sync_fns
    decorators._sync_fns = {
        et: AsyncMock()
        for et in (
            EntityType.SUPPLIER,
            EntityType.LOCATION,
            EntityType.TAX_RATE,
            EntityType.OPERATOR,
            EntityType.ADDITIONAL_COST,
        )
    }
    try:
        yield
    finally:
        decorators._sync_fns = original


# ============================================================================
# Helpers
# ============================================================================


def _extract_text(tool_result: ToolResult) -> str:
    """Return the text payload from the first ``TextContent`` block."""
    assert tool_result.content, "ToolResult.content is empty"
    block = tool_result.content[0]
    assert isinstance(block, TextContent), (
        f"Expected TextContent, got {type(block).__name__}"
    )
    return block.text


def _make_context(
    *,
    get_all: list[dict] | None = None,
    smart_search: list[dict] | None = None,
    get_by_id: dict | None = None,
):
    """Mock context with cache methods primed for the test."""
    context, lifespan_ctx = create_mock_context()
    if get_all is not None:
        lifespan_ctx.cache.get_all = AsyncMock(return_value=get_all)
    if smart_search is not None:
        lifespan_ctx.cache.smart_search = AsyncMock(return_value=smart_search)
    if get_by_id is not None:
        lifespan_ctx.cache.get_by_id = AsyncMock(return_value=get_by_id)
    return context, lifespan_ctx


# ============================================================================
# list_suppliers
# ============================================================================


class TestListSuppliers:
    @pytest.mark.asyncio
    async def test_no_query_uses_get_all_and_filters_deleted(self):
        cached = [
            {"id": 1, "name": "Acme", "email": "a@acme.com", "currency": "USD"},
            {
                "id": 2,
                "name": "RetiredCo",
                "email": "x@retired.com",
                "deleted_at": "2026-01-01T00:00:00Z",
            },
            {"id": 3, "name": "BetaCo", "code": "BETA"},
        ]
        context, lifespan_ctx = _make_context(get_all=cached)

        result = await list_suppliers(
            query=None, limit=50, format="json", context=context
        )

        assert lifespan_ctx.cache.get_all.await_count == 1
        # smart_search must NOT be called when query is None
        assert lifespan_ctx.cache.smart_search.await_count == 0

        payload = json.loads(_extract_text(result))
        assert len(payload["suppliers"]) == 2
        assert payload["total_count"] == 2  # post-deleted-filter total
        assert {s["id"] for s in payload["suppliers"]} == {1, 3}
        assert payload["query"] is None

    @pytest.mark.asyncio
    async def test_query_uses_smart_search_not_get_all(self):
        matches = [
            {"id": 7, "name": "SRAM", "email": "kemmett@sram.com", "code": "SRAM-01"},
        ]
        context, lifespan_ctx = _make_context(smart_search=matches, get_all=[])

        result = await list_suppliers(
            query="SRAM", limit=10, format="json", context=context
        )

        # Query path must use FTS, not full-list dump
        assert lifespan_ctx.cache.smart_search.await_count == 1
        assert lifespan_ctx.cache.get_all.await_count == 0
        smart_call = lifespan_ctx.cache.smart_search.await_args
        assert smart_call.args[0] == "supplier"
        assert smart_call.args[1] == "SRAM"
        assert smart_call.kwargs["limit"] == 10

        payload = json.loads(_extract_text(result))
        assert len(payload["suppliers"]) == 1
        assert payload["suppliers"][0]["id"] == 7
        assert payload["query"] == "SRAM"

    @pytest.mark.asyncio
    async def test_limit_caps_no_query_path(self):
        cached = [{"id": i, "name": f"Supplier-{i}"} for i in range(1, 21)]
        context, _ = _make_context(get_all=cached)

        result = await list_suppliers(
            query=None, limit=5, format="json", context=context
        )

        payload = json.loads(_extract_text(result))
        assert len(payload["suppliers"]) == 5
        # total_count reflects pre-limit count so callers see "5 of 20"
        assert payload["total_count"] == 20

    @pytest.mark.asyncio
    async def test_markdown_format_renders_bounded_summary_not_giant_blob(self):
        cached = [{"id": 1, "name": "Acme", "email": "a@acme.com", "currency": "USD"}]
        context, _ = _make_context(get_all=cached)

        result = await list_suppliers(
            query=None, limit=50, format="markdown", context=context
        )

        text = _extract_text(result)
        assert "## Suppliers" in text
        assert "Acme" in text
        assert "ID: 1" in text
        # Markdown output is bullet-list — must not be a JSON dump
        assert not text.lstrip().startswith("{")

    @pytest.mark.asyncio
    async def test_empty_result_no_query(self):
        context, _ = _make_context(get_all=[])
        result = await list_suppliers(
            query=None, limit=50, format="markdown", context=context
        )
        assert "No suppliers cached" in _extract_text(result)

    @pytest.mark.asyncio
    async def test_empty_result_with_query(self):
        context, _ = _make_context(smart_search=[])
        result = await list_suppliers(
            query="NoSuchSupplier",
            limit=10,
            format="markdown",
            context=context,
        )
        text = _extract_text(result)
        assert "No suppliers found matching" in text
        assert "NoSuchSupplier" in text

    @pytest.mark.asyncio
    async def test_query_path_filters_soft_deleted(self):
        """smart_search results must drop deleted_at rows — symmetric with
        the no-query path. Without this filter, an FTS hit on a soft-
        deleted supplier would surface in the response.
        """
        matches = [
            {"id": 1, "name": "ActiveCo", "code": "AC"},
            {
                "id": 2,
                "name": "TombstonedCo",
                "code": "AC",
                "deleted_at": "2026-01-01T00:00:00Z",
            },
        ]
        context, _ = _make_context(smart_search=matches)

        result = await list_suppliers(
            query="AC", limit=10, format="json", context=context
        )

        payload = json.loads(_extract_text(result))
        assert {s["id"] for s in payload["suppliers"]} == {1}
        assert payload["total_count"] == 1

    @pytest.mark.asyncio
    async def test_whitespace_only_query_treated_as_no_query(self):
        """``query="   "`` falls through to ``get_all`` (not smart_search)
        and ``response.query`` ends up ``None`` — so the markdown header
        renders the no-query form, not "query `   `".
        """
        cached = [{"id": 1, "name": "Acme"}]
        context, lifespan_ctx = _make_context(get_all=cached, smart_search=[])

        result = await list_suppliers(
            query="   ", limit=50, format="markdown", context=context
        )

        # Whitespace-only query must NOT trigger smart_search
        assert lifespan_ctx.cache.smart_search.await_count == 0
        assert lifespan_ctx.cache.get_all.await_count == 1

        text = _extract_text(result)
        # Header should be the no-query form ("## Suppliers (1 of 1)"),
        # not "query `   `"
        assert "query" not in text.lower()
        assert "Acme" in text


# ============================================================================
# get_supplier
# ============================================================================


class TestGetSupplier:
    @pytest.mark.asyncio
    async def test_returns_full_detail(self):
        record = {
            "id": 1302095,
            "name": "SRAM",
            "email": "kemmett@example.com",
            "phone": "555-0100",
            "currency": "USD",
            "code": "SRAM-01",
            "comment": "Primary drivetrain supplier.",
            "default_payment_terms": "Net 30",
            "address_line_1": "1 SRAM Way",
            "city": "Chicago",
            "state": "IL",
            "zip": "60601",
            "country": "US",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2026-01-15T00:00:00Z",
        }
        context, lifespan_ctx = _make_context(get_by_id=record)

        result = await get_supplier(supplier_id=1302095, format="json", context=context)

        lifespan_ctx.cache.get_by_id.assert_awaited_once_with("supplier", 1302095)
        payload = json.loads(_extract_text(result))
        assert payload["id"] == 1302095
        assert payload["name"] == "SRAM"
        assert payload["default_payment_terms"] == "Net 30"
        assert payload["city"] == "Chicago"
        assert payload["country"] == "US"

    @pytest.mark.asyncio
    async def test_not_found_raises_value_error(self):
        context, _ = _make_context(get_by_id=None)
        with pytest.raises(ValueError, match="Supplier with ID 999 not found"):
            await get_supplier(supplier_id=999, format="json", context=context)

    @pytest.mark.asyncio
    async def test_markdown_format_renders_card(self):
        record = {"id": 1, "name": "Acme", "email": "a@acme.com", "currency": "USD"}
        context, _ = _make_context(get_by_id=record)
        result = await get_supplier(supplier_id=1, format="markdown", context=context)
        text = _extract_text(result)
        assert "## Acme" in text
        assert "**email**: a@acme.com" in text
        assert "**currency**: USD" in text


# ============================================================================
# list_locations
# ============================================================================


class TestListLocations:
    @pytest.mark.asyncio
    async def test_query_uses_smart_search(self):
        context, lifespan_ctx = _make_context(
            smart_search=[
                {
                    "id": 100,
                    "name": "Main Warehouse",
                    "address": {
                        "id": 9,
                        "line_1": "1 Industrial Way",
                        "line_2": "Suite 4",
                        "city": "Portland",
                        "state": "OR",
                        "zip": "97201",
                        "country": "US",
                    },
                    "is_primary": True,
                }
            ]
        )
        result = await list_locations(
            query="Main", limit=5, format="json", context=context
        )
        lifespan_ctx.cache.smart_search.assert_awaited_once()
        payload = json.loads(_extract_text(result))
        loc = payload["locations"][0]
        assert loc["is_primary"] is True
        assert loc["address"] == {
            "line_1": "1 Industrial Way",
            "line_2": "Suite 4",
            "city": "Portland",
            "state": "OR",
            "zip": "97201",
            "country": "US",
        }

    @pytest.mark.asyncio
    async def test_markdown_renders_city_country_from_nested_address(self):
        context, _ = _make_context(
            get_all=[
                {
                    "id": 24141,
                    "name": "Goleta DC",
                    "address": {"city": "Goleta", "country": "US"},
                }
            ]
        )
        result = await list_locations(
            query=None, limit=50, format="markdown", context=context
        )
        text = _extract_text(result)
        assert "Goleta DC" in text
        assert "Goleta, US" in text

    @pytest.mark.asyncio
    async def test_missing_address_yields_none(self):
        context, _ = _make_context(get_all=[{"id": 1, "name": "No-address site"}])
        result = await list_locations(
            query=None, limit=50, format="json", context=context
        )
        payload = json.loads(_extract_text(result))
        assert payload["locations"][0]["address"] is None

    @pytest.mark.asyncio
    async def test_blank_string_address_parts_collapse_to_none(self):
        """Katana sometimes returns blank address parts as ``""`` rather than
        omitting them — the all-empty case must still collapse to
        ``address: null`` instead of an AddressInfo full of empty strings.
        Also pins that a non-blank line_1 alongside blank-only siblings
        still yields a populated address with the empties normalized away.
        """
        context, _ = _make_context(
            get_all=[
                {
                    "id": 1,
                    "name": "All-blank address",
                    "address": {
                        "id": 9,
                        "line_1": "",
                        "line_2": "   ",
                        "city": "",
                        "state": "",
                        "zip": "",
                        "country": "",
                    },
                },
                {
                    "id": 2,
                    "name": "Partially-populated address",
                    "address": {
                        "line_1": "1 Main St",
                        "line_2": "",
                        "city": "Goleta",
                        "state": "  ",
                        "zip": None,
                        "country": "US",
                    },
                },
            ]
        )
        result = await list_locations(
            query=None, limit=50, format="json", context=context
        )
        payload = json.loads(_extract_text(result))
        assert payload["locations"][0]["address"] is None
        assert payload["locations"][1]["address"] == {
            "line_1": "1 Main St",
            "line_2": None,
            "city": "Goleta",
            "state": None,
            "zip": None,
            "country": "US",
        }

    @pytest.mark.asyncio
    async def test_no_query_filters_deleted(self):
        cached = [
            {"id": 1, "name": "Active"},
            {
                "id": 2,
                "name": "Closed",
                "deleted_at": "2026-01-01T00:00:00Z",
            },
        ]
        context, _ = _make_context(get_all=cached)
        result = await list_locations(
            query=None, limit=50, format="json", context=context
        )
        payload = json.loads(_extract_text(result))
        assert len(payload["locations"]) == 1
        assert payload["locations"][0]["id"] == 1


# ============================================================================
# list_tax_rates / list_operators / list_additional_costs
# ============================================================================


class TestSmallReferenceTools:
    """Smaller tools share the same shape; one round-trip test each."""

    @pytest.mark.asyncio
    async def test_list_tax_rates_returns_summary(self):
        context, _ = _make_context(
            get_all=[
                {
                    "id": 1,
                    "name": "Standard",
                    "rate": 8.5,
                    "is_default_sales": True,
                }
            ]
        )
        result = await list_tax_rates(
            query=None, limit=50, format="json", context=context
        )
        payload = json.loads(_extract_text(result))
        assert payload["tax_rates"][0]["rate"] == 8.5
        assert payload["tax_rates"][0]["is_default_sales"] is True

    @pytest.mark.asyncio
    async def test_list_operators_returns_summary(self):
        context, _ = _make_context(
            get_all=[{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        )
        result = await list_operators(
            query=None, limit=50, format="json", context=context
        )
        payload = json.loads(_extract_text(result))
        assert {op["name"] for op in payload["operators"]} == {"Alice", "Bob"}

    @pytest.mark.asyncio
    async def test_list_additional_costs_returns_summary(self):
        context, _ = _make_context(
            get_all=[
                {"id": 1, "name": "Shipping"},
                {"id": 2, "name": "Import Duty"},
            ]
        )
        result = await list_additional_costs(
            query=None, limit=50, format="json", context=context
        )
        payload = json.loads(_extract_text(result))
        assert {ac["name"] for ac in payload["additional_costs"]} == {
            "Shipping",
            "Import Duty",
        }


# ============================================================================
# Request-model contracts
# ============================================================================


class TestRequestModels:
    """Pydantic request models gate inputs before the tool runs."""

    def test_limit_clamped_to_max(self):
        """Limit > 250 is rejected (guards against bulk dumps)."""
        with pytest.raises(ValueError):
            ListSuppliersRequest(limit=251)

    def test_limit_clamped_to_min(self):
        with pytest.raises(ValueError):
            ListSuppliersRequest(limit=0)

    def test_format_must_be_known(self):
        with pytest.raises(ValueError):
            ListSuppliersRequest.model_validate({"format": "xml"})

    def test_extra_fields_forbidden(self):
        """``extra="forbid"`` keeps callers honest about parameter names."""
        with pytest.raises(ValueError):
            ListSuppliersRequest.model_validate({"querystr": "SRAM"})

    def test_default_query_is_none_default_format_markdown(self):
        req = ListSuppliersRequest()
        assert req.query is None
        assert req.limit == 50
        assert req.format == "markdown"

    def test_get_supplier_requires_id(self):
        with pytest.raises(ValueError):
            GetSupplierRequest()  # type: ignore[call-arg]

    @pytest.mark.parametrize(
        "model",
        [
            ListLocationsRequest,
            ListTaxRatesRequest,
            ListOperatorsRequest,
            ListAdditionalCostsRequest,
        ],
    )
    def test_peer_models_share_shape(self, model):
        """Every reference list-tool request model has the same defaults."""
        req = model()
        assert req.query is None
        assert req.limit == 50
        assert req.format == "markdown"


# ============================================================================
# Registration
# ============================================================================


class TestRegistration:
    def test_registers_six_tools(self):
        """register_tools wires up 5 list_* tools + get_supplier."""
        mcp = MagicMock()
        tool_decorator = MagicMock(side_effect=lambda fn: fn)
        mcp.tool = MagicMock(return_value=tool_decorator)

        register_tools(mcp)

        assert mcp.tool.call_count == 6
        for call in mcp.tool.call_args_list:
            assert "reference" in call.kwargs["tags"]
            assert "read" in call.kwargs["tags"]
            ann = call.kwargs["annotations"]
            assert ann.readOnlyHint is True
            assert ann.destructiveHint is False
            assert ann.idempotentHint is True

        decorated = {call.args[0].__name__ for call in tool_decorator.call_args_list}
        assert decorated == {
            "list_locations",
            "list_suppliers",
            "get_supplier",
            "list_tax_rates",
            "list_operators",
            "list_additional_costs",
        }
