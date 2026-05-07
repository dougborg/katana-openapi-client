"""Tests for reference-data tool wrappers (`list_locations`, `list_suppliers`,
`list_tax_rates`, `list_operators`, `list_additional_costs`).

Each tool is a thin wrapper around the corresponding resource handler in
``katana_mcp.resources.reference``. These tests assert that the tool returns
the **same data** as reading the resource directly — the contract callers
rely on for swapping between surfaces.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.tools import ToolResult
from katana_mcp.resources.reference import (
    get_additional_costs,
    get_locations,
    get_operators,
    get_suppliers,
    get_tax_rates,
)
from katana_mcp.tools.foundation.reference import (
    list_additional_costs,
    list_locations,
    list_operators,
    list_suppliers,
    list_tax_rates,
    register_tools,
)
from mcp.types import TextContent

from tests.conftest import create_mock_context


def _extract_text(tool_result: ToolResult) -> str:
    """Return the text payload from the first ``TextContent`` block.

    Tool results are stored as a list of content blocks (text, image, etc.).
    Reference tools always emit a single JSON-serialized text block — this
    helper unwraps it for the assertion.
    """
    assert tool_result.content, "ToolResult.content is empty"
    block = tool_result.content[0]
    assert isinstance(block, TextContent), (
        f"Expected TextContent, got {type(block).__name__}"
    )
    return block.text


def _make_context_with_cache(cached_entities: list[dict]):
    """Mock context whose CatalogCache returns a fixed list from ``get_all``."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_all = AsyncMock(return_value=cached_entities)
    return context


# ============================================================================
# Tool/resource parity — the core contract these tools exist to honor
# ============================================================================


class TestToolResourceParity:
    """Each ``list_*`` tool must return the same data as calling the
    corresponding resource handler directly. The tool serializes through
    ``ToolResult`` (content + structured_content); both surfaces must agree.
    """

    @pytest.mark.asyncio
    async def test_list_locations_matches_resource(self):
        cached = [
            {
                "id": 100,
                "name": "Main Warehouse",
                "address": "123 Industrial Way",
                "city": "Portland",
                "country": "US",
                "is_primary": True,
            },
            {
                "id": 101,
                "name": "Satellite",
                "address": "456 Side St",
                "city": "Eugene",
                "country": "US",
                "is_primary": False,
            },
        ]
        context = _make_context_with_cache(cached)
        with patch(
            "katana_mcp.resources.reference.ensure_locations_synced",
            new_callable=AsyncMock,
        ):
            resource_payload = json.loads(await get_locations(context))
        # Re-mock the cache for the second call (AsyncMock state stays fine,
        # but a fresh resource sync needs patching for the tool's call too).
        with patch(
            "katana_mcp.resources.reference.ensure_locations_synced",
            new_callable=AsyncMock,
        ):
            tool_result = await list_locations(context)

        assert isinstance(tool_result, ToolResult)
        assert tool_result.structured_content is not None
        # `summary` and the data list must match between surfaces. (The
        # `generated_at` timestamps differ between the two calls — that's
        # expected and not part of the contract.)
        assert tool_result.structured_content["summary"] == resource_payload["summary"]
        assert (
            tool_result.structured_content["locations"] == resource_payload["locations"]
        )
        # Content blocks expose the JSON payload as text; it must round-trip
        # to the same structured payload.
        assert json.loads(_extract_text(tool_result)) == tool_result.structured_content

    @pytest.mark.asyncio
    async def test_list_suppliers_matches_resource(self):
        cached = [
            {
                "id": 1,
                "name": "Acme Corp",
                "email": "sales@acme.com",
                "phone": "555-0100",
                "currency": "USD",
                "comment": None,
            },
        ]
        context = _make_context_with_cache(cached)
        with patch(
            "katana_mcp.resources.reference.ensure_suppliers_synced",
            new_callable=AsyncMock,
        ):
            resource_payload = json.loads(await get_suppliers(context))
        with patch(
            "katana_mcp.resources.reference.ensure_suppliers_synced",
            new_callable=AsyncMock,
        ):
            tool_result = await list_suppliers(context)

        assert tool_result.structured_content is not None
        assert tool_result.structured_content["summary"] == resource_payload["summary"]
        assert (
            tool_result.structured_content["suppliers"] == resource_payload["suppliers"]
        )

    @pytest.mark.asyncio
    async def test_list_tax_rates_matches_resource(self):
        cached = [
            {
                "id": 1,
                "name": "Standard",
                "rate": 8.5,
                "display_name": "CA Sales Tax",
                "is_default_sales": True,
                "is_default_purchases": False,
            },
        ]
        context = _make_context_with_cache(cached)
        with patch(
            "katana_mcp.resources.reference.ensure_tax_rates_synced",
            new_callable=AsyncMock,
        ):
            resource_payload = json.loads(await get_tax_rates(context))
        with patch(
            "katana_mcp.resources.reference.ensure_tax_rates_synced",
            new_callable=AsyncMock,
        ):
            tool_result = await list_tax_rates(context)

        assert tool_result.structured_content is not None
        assert tool_result.structured_content["summary"] == resource_payload["summary"]
        assert (
            tool_result.structured_content["tax_rates"] == resource_payload["tax_rates"]
        )

    @pytest.mark.asyncio
    async def test_list_operators_matches_resource(self):
        cached = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        context = _make_context_with_cache(cached)
        with patch(
            "katana_mcp.resources.reference.ensure_operators_synced",
            new_callable=AsyncMock,
        ):
            resource_payload = json.loads(await get_operators(context))
        with patch(
            "katana_mcp.resources.reference.ensure_operators_synced",
            new_callable=AsyncMock,
        ):
            tool_result = await list_operators(context)

        assert tool_result.structured_content is not None
        assert tool_result.structured_content["summary"] == resource_payload["summary"]
        assert (
            tool_result.structured_content["operators"] == resource_payload["operators"]
        )

    @pytest.mark.asyncio
    async def test_list_additional_costs_matches_resource(self):
        cached = [
            {"id": 1, "name": "Shipping Cost"},
            {"id": 2, "name": "Import Duty"},
        ]
        context = _make_context_with_cache(cached)
        with patch(
            "katana_mcp.resources.reference.ensure_additional_costs_synced",
            new_callable=AsyncMock,
        ):
            resource_payload = json.loads(await get_additional_costs(context))
        with patch(
            "katana_mcp.resources.reference.ensure_additional_costs_synced",
            new_callable=AsyncMock,
        ):
            tool_result = await list_additional_costs(context)

        assert tool_result.structured_content is not None
        assert tool_result.structured_content["summary"] == resource_payload["summary"]
        assert (
            tool_result.structured_content["additional_costs"]
            == resource_payload["additional_costs"]
        )


# ============================================================================
# Registration
# ============================================================================


class TestRegistration:
    def test_registers_all_five_tools(self):
        """``register_tools`` must register exactly the 5 reference tools."""
        mcp = MagicMock()
        # ``mcp.tool`` is called as ``mcp.tool(tags=..., annotations=...)``,
        # which returns a decorator that wraps the tool function.
        tool_decorator = MagicMock(side_effect=lambda fn: fn)
        mcp.tool = MagicMock(return_value=tool_decorator)

        register_tools(mcp)

        # Five tool decorators should have been created
        assert mcp.tool.call_count == 5
        # All registered tools should be tagged 'reference' + 'read'
        for call in mcp.tool.call_args_list:
            assert "reference" in call.kwargs["tags"]
            assert "read" in call.kwargs["tags"]
            # All annotations should mark the tools read-only and idempotent
            ann = call.kwargs["annotations"]
            assert ann.readOnlyHint is True
            assert ann.destructiveHint is False
            assert ann.idempotentHint is True

        # Each of the 5 tool functions should have been passed through the
        # decorator returned by ``mcp.tool(...)``.
        decorated = {call.args[0].__name__ for call in tool_decorator.call_args_list}
        assert decorated == {
            "list_locations",
            "list_suppliers",
            "list_tax_rates",
            "list_operators",
            "list_additional_costs",
        }
