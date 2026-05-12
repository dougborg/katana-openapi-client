"""Tests for parameterized reference-data tools."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastmcp.tools import ToolResult
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

from katana_public_api_client.models_pydantic._generated import (
    CachedAdditionalCost,
    CachedLocation,
    CachedOperator,
    CachedSupplier,
    CachedTaxRate,
)


@pytest.fixture(autouse=True)
def _patch_cache_sync():
    """Stub @cache_read sync fns so cache reads don't trigger API fetches.

    Direct dict replacement (not patch.dict): the decorator caches its
    Cached* class → sync_fn map by reference on first call, so patching
    the typed_cache.sync module after the dict is populated has no effect.
    """
    original = decorators._sync_fns
    decorators._sync_fns = {
        cls: AsyncMock()
        for cls in (
            CachedSupplier,
            CachedLocation,
            CachedTaxRate,
            CachedOperator,
            CachedAdditionalCost,
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
    get_all: list[Any] | None = None,
    smart_search: list[Any] | None = None,
    get_by_id: Any | None = None,
):
    """Mock context with typed-cache catalog methods primed for the test."""
    context, lifespan_ctx = create_mock_context()
    if get_all is not None:
        lifespan_ctx.typed_cache.catalog.get_all = AsyncMock(return_value=get_all)
    if smart_search is not None:
        lifespan_ctx.typed_cache.catalog.smart_search = AsyncMock(
            return_value=smart_search
        )
    if get_by_id is not None:
        lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(return_value=get_by_id)
    return context, lifespan_ctx


def _supplier(**fields: Any) -> CachedSupplier:
    fields.setdefault("id", 1)
    fields.setdefault("name", "Test Supplier")
    return CachedSupplier(**fields)


def _location(**fields: Any) -> CachedLocation:
    fields.setdefault("id", 1)
    fields.setdefault("name", "Test Location")
    return CachedLocation(**fields)


def _tax_rate(**fields: Any) -> CachedTaxRate:
    fields.setdefault("id", 1)
    fields.setdefault("name", "Test Tax Rate")
    return CachedTaxRate(**fields)


def _operator(**fields: Any) -> CachedOperator:
    fields.setdefault("id", 1)
    fields.setdefault("operator_name", "Test Operator")
    return CachedOperator(**fields)


def _additional_cost(**fields: Any) -> CachedAdditionalCost:
    fields.setdefault("id", 1)
    fields.setdefault("name", "Test Cost")
    return CachedAdditionalCost(**fields)


# ============================================================================
# list_suppliers
# ============================================================================


class TestListSuppliers:
    """The catalog adapter's ``get_all`` and ``smart_search`` already
    push ``deleted_at IS NULL`` down to SQL (default
    ``include_deleted=False``), so the per-tool soft-delete filter from
    the legacy cache is gone. Tests below pin the routing semantics
    (query → smart_search, no-query → get_all, etc.) and the response
    shape, but no longer fixture in soft-deleted rows that the
    adapter would have already dropped.
    """

    @pytest.mark.asyncio
    async def test_no_query_uses_get_all(self):
        cached = [
            _supplier(id=1, name="Acme", email="a@acme.com", currency="USD"),
            _supplier(id=3, name="BetaCo"),
        ]
        context, lifespan_ctx = _make_context(get_all=cached)

        result = await list_suppliers(
            query=None, limit=50, format="json", context=context
        )

        assert lifespan_ctx.typed_cache.catalog.get_all.await_count == 1
        # smart_search must NOT be called when query is None
        assert lifespan_ctx.typed_cache.catalog.smart_search.await_count == 0

        payload = json.loads(_extract_text(result))
        assert len(payload["suppliers"]) == 2
        assert payload["total_count"] == 2
        assert {s["id"] for s in payload["suppliers"]} == {1, 3}
        assert payload["query"] is None

    @pytest.mark.asyncio
    async def test_query_uses_smart_search_not_get_all(self):
        matches = [
            _supplier(
                id=7, name="Acme Components", email="contact@acme-components.example"
            )
        ]
        context, lifespan_ctx = _make_context(smart_search=matches, get_all=[])

        result = await list_suppliers(
            query="Acme Components", limit=10, format="json", context=context
        )

        # Query path must use FTS, not full-list dump
        assert lifespan_ctx.typed_cache.catalog.smart_search.await_count == 1
        assert lifespan_ctx.typed_cache.catalog.get_all.await_count == 0
        smart_call = lifespan_ctx.typed_cache.catalog.smart_search.await_args
        # First positional arg is the Cached* class, second is the query.
        assert smart_call.args[0] is CachedSupplier
        assert smart_call.args[1] == "Acme Components"
        assert smart_call.kwargs["limit"] == 10

        payload = json.loads(_extract_text(result))
        assert len(payload["suppliers"]) == 1
        assert payload["suppliers"][0]["id"] == 7
        assert payload["query"] == "Acme Components"

    @pytest.mark.asyncio
    async def test_limit_caps_no_query_path(self):
        cached = [_supplier(id=i, name=f"Supplier-{i}") for i in range(1, 21)]
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
        cached = [_supplier(id=1, name="Acme", email="a@acme.com", currency="USD")]
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
    async def test_whitespace_only_query_treated_as_no_query(self):
        """``query="   "`` falls through to ``get_all`` (not smart_search)
        and ``response.query`` ends up ``None`` — so the markdown header
        renders the no-query form, not "query `   `".
        """
        cached = [_supplier(id=1, name="Acme")]
        context, lifespan_ctx = _make_context(get_all=cached, smart_search=[])

        result = await list_suppliers(
            query="   ", limit=50, format="markdown", context=context
        )

        # Whitespace-only query must NOT trigger smart_search
        assert lifespan_ctx.typed_cache.catalog.smart_search.await_count == 0
        assert lifespan_ctx.typed_cache.catalog.get_all.await_count == 1

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
        from datetime import datetime

        record = _supplier(
            id=1302095,
            name="Acme Components",
            email="contact@acme-components.example",
            phone="555-0100",
            currency="USD",
            comment="Primary component supplier.",
            created_at=datetime(2024, 1, 1),
            updated_at=datetime(2026, 1, 15),
        )
        context, lifespan_ctx = _make_context(get_by_id=record)

        result = await get_supplier(supplier_id=1302095, format="json", context=context)

        # Adapter takes the Cached* class as the first positional arg.
        await_args = lifespan_ctx.typed_cache.catalog.get_by_id.await_args
        assert await_args.args[0] is CachedSupplier
        assert await_args.args[1] == 1302095
        payload = json.loads(_extract_text(result))
        assert payload["id"] == 1302095
        assert payload["name"] == "Acme Components"
        assert payload["currency"] == "USD"
        # Fields that the wire ``Supplier`` schema doesn't carry default to None.
        assert payload["default_payment_terms"] is None
        assert payload["city"] is None
        assert payload["country"] is None

    @pytest.mark.asyncio
    async def test_not_found_raises_value_error(self):
        # Re-attach to a fresh context; create_mock_context yields fresh mocks
        # per call so this is the canonical "supplier not in cache" path.
        context2, lifespan_ctx2 = create_mock_context()
        lifespan_ctx2.typed_cache.catalog.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(ValueError, match="Supplier with ID 999 not found"):
            await get_supplier(supplier_id=999, format="json", context=context2)

    @pytest.mark.asyncio
    async def test_markdown_format_renders_card(self):
        record = _supplier(id=1, name="Acme", email="a@acme.com", currency="USD")
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
        from katana_public_api_client.models_pydantic._generated import (
            LocationAddress,
        )

        loc = _location(
            id=100,
            name="Main Warehouse",
            address=LocationAddress(
                id=9,
                line_1="1 Industrial Way",
                line_2="Suite 4",
                city="Portland",
                state="OR",
                zip="97201",
                country="US",
            ),
            is_primary=True,
        )
        context, lifespan_ctx = _make_context(smart_search=[loc])
        result = await list_locations(
            query="Main", limit=5, format="json", context=context
        )
        lifespan_ctx.typed_cache.catalog.smart_search.assert_awaited_once()
        payload = json.loads(_extract_text(result))
        loc_payload = payload["locations"][0]
        assert loc_payload["is_primary"] is True
        assert loc_payload["address"] == {
            "line_1": "1 Industrial Way",
            "line_2": "Suite 4",
            "city": "Portland",
            "state": "OR",
            "zip": "97201",
            "country": "US",
        }

    @pytest.mark.asyncio
    async def test_markdown_renders_city_country_from_nested_address(self):
        # Bypass pydantic validation on the JSON column — the helper's
        # ``_address_from_obj`` accepts either ``LocationAddress`` or a
        # raw dict, and it's the dict shape that exercises the partial-
        # field path (a real wire ``LocationAddress`` would carry every
        # required field).
        loc = _location(id=24141, name="Goleta DC")
        object.__setattr__(loc, "address", {"city": "Goleta", "country": "US"})
        context, _ = _make_context(get_all=[loc])
        result = await list_locations(
            query=None, limit=50, format="markdown", context=context
        )
        text = _extract_text(result)
        assert "Goleta DC" in text
        assert "Goleta, US" in text

    @pytest.mark.asyncio
    async def test_missing_address_yields_none(self):
        context, _ = _make_context(get_all=[_location(id=1, name="No-address site")])
        result = await list_locations(
            query=None, limit=50, format="json", context=context
        )
        payload = json.loads(_extract_text(result))
        assert payload["locations"][0]["address"] is None

    @pytest.mark.asyncio
    async def test_blank_string_address_parts_collapse_to_none(self):
        """Katana sometimes returns blank address parts as ``""`` (notably
        ``line_2``) rather than omitting them — the cleaning helper
        must whitespace-collapse those to ``None`` so callers don't
        render ``line_2: ""`` artifacts.

        Constructs the row's ``address`` as a dict and bypasses
        pydantic validation by setting it post-construction — the
        typed ``LocationAddress`` validators reject empty strings on
        required fields like ``city``/``zip``, but the cache JSON column
        round-trips arbitrary shapes via ``model_dump`` and the
        cleaning helper has to handle whatever comes back.
        """
        loc = _location(id=2, name="Partially-populated address")
        # Bypass pydantic validation on the JSON column — the helper's
        # job is to handle the raw dict shape that comes off the wire.
        object.__setattr__(
            loc,
            "address",
            {
                "line_1": "1 Main St",
                "line_2": "",  # whitespace-empty → None
                "city": "Goleta",
                "state": "  ",  # whitespace-only → None
                "zip": None,
                "country": "US",
            },
        )
        context, _ = _make_context(get_all=[loc])
        result = await list_locations(
            query=None, limit=50, format="json", context=context
        )
        payload = json.loads(_extract_text(result))
        assert payload["locations"][0]["address"] == {
            "line_1": "1 Main St",
            "line_2": None,
            "city": "Goleta",
            "state": None,
            "zip": None,
            "country": "US",
        }


# ============================================================================
# list_tax_rates / list_operators / list_additional_costs
# ============================================================================


class TestSmallReferenceTools:
    """Smaller tools share the same shape; one round-trip test each."""

    @pytest.mark.asyncio
    async def test_list_tax_rates_returns_summary(self):
        context, _ = _make_context(
            get_all=[
                _tax_rate(
                    id=1,
                    name="Standard",
                    rate=8.5,
                    is_default_sales=True,
                )
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
            get_all=[
                _operator(id=1, operator_name="Alice"),
                _operator(id=2, operator_name="Bob"),
            ]
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
                _additional_cost(id=1, name="Shipping"),
                _additional_cost(id=2, name="Import Duty"),
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
            ListSuppliersRequest.model_validate({"querystr": "Acme Components"})

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
