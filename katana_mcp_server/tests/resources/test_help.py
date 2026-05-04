"""Tests for the four help resources (``katana://help``, ``katana://help/workflows``,
``katana://help/tools``, ``katana://help/resources``).

The handlers themselves are trivial — they return precomputed module-level
strings. The contract these tests pin is the *content invariant*: the
help docs name the major capability areas an agent should be able to
discover (preview/apply pattern, modify_<entity> pattern, the tool
families). If a future refactor accidentally truncates a help string or
swaps the wrong constant into a registration, these tests fail.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from katana_mcp.resources.help import (
    HELP_INDEX,
    HELP_RESOURCES,
    HELP_TOOLS,
    HELP_WORKFLOWS,
    get_help_index,
    get_help_resources,
    get_help_tools,
    get_help_workflows,
    register_resources,
)

# ============================================================================
# Per-handler return contract
# ============================================================================


@pytest.mark.asyncio
async def test_help_index_returns_precomputed_string():
    result = await get_help_index()
    assert result == HELP_INDEX
    assert isinstance(result, str)
    assert result.strip(), "Help index must not be empty"


@pytest.mark.asyncio
async def test_help_workflows_returns_precomputed_string():
    result = await get_help_workflows()
    assert result == HELP_WORKFLOWS
    assert isinstance(result, str)
    assert result.strip(), "Help workflows must not be empty"


@pytest.mark.asyncio
async def test_help_tools_returns_precomputed_string():
    result = await get_help_tools()
    assert result == HELP_TOOLS
    assert isinstance(result, str)
    assert result.strip(), "Help tools must not be empty"


@pytest.mark.asyncio
async def test_help_resources_returns_precomputed_string():
    result = await get_help_resources()
    assert result == HELP_RESOURCES
    assert isinstance(result, str)
    assert result.strip(), "Help resources must not be empty"


# ============================================================================
# Content invariants — guard against accidental truncation / wrong constant
# ============================================================================


class TestHelpIndexContent:
    """Pins the high-level capability areas the index advertises. These
    are the structural anchors a future contributor would notice if they
    accidentally swapped or truncated the index string.
    """

    def test_lists_core_capability_sections(self):
        # All four major sections an agent uses to navigate the server.
        assert "Inventory & Catalog" in HELP_INDEX
        assert "Purchase Orders" in HELP_INDEX
        assert "Manufacturing & Sales" in HELP_INDEX
        assert "Stock Transfers" in HELP_INDEX

    def test_documents_preview_apply_safety_pattern(self):
        # The preview/apply pattern is the single most important contract
        # for agents to learn — if this drops out, agents will skip the
        # preview step and write directly. Pin it.
        assert "preview/apply" in HELP_INDEX or "preview=true" in HELP_INDEX
        assert "preview=false" in HELP_INDEX

    def test_links_to_subsections(self):
        # The index is meant to enable progressive discovery. Each
        # subsection URL must be reachable from the index.
        assert "katana://help/workflows" in HELP_INDEX
        assert "katana://help/tools" in HELP_INDEX
        assert "katana://help/resources" in HELP_INDEX


class TestHelpWorkflowsContent:
    def test_lists_canonical_workflows(self):
        # The five canonical workflows the prompts module also exposes.
        # If these drift, the docs and the prompts diverge.
        assert "Reorder" in HELP_WORKFLOWS or "Reorder Low Stock" in HELP_WORKFLOWS
        assert "Receive Purchase Order" in HELP_WORKFLOWS
        assert "Manufacturing Order" in HELP_WORKFLOWS
        assert "Sales Order" in HELP_WORKFLOWS


class TestHelpToolsContent:
    def test_documents_at_least_one_create_tool(self):
        # Sanity: the tools doc must mention at least one of the create
        # tools whose contract is documented elsewhere as preview/apply.
        assert "create_purchase_order" in HELP_TOOLS


class TestHelpResourcesContent:
    def test_documents_at_least_one_resource(self):
        # The resources doc must reference at least the inventory items
        # resource — that's the canonical cache-backed read path agents
        # use to browse the catalog.
        assert "inventory" in HELP_RESOURCES.lower()


# ============================================================================
# Registration
# ============================================================================


def _capture_registrations(mcp) -> list[tuple[dict, object]]:
    """Capture both registration kwargs and decorated handlers.

    ``mcp.resource(uri=...)`` returns a decorator that's called with the
    handler — a ``MagicMock(return_value=lambda fn: fn)`` style mock
    discards the handler. We record both halves so URI→handler
    mismatches (like registering ``katana://help/tools`` against
    ``get_help_resources``) fail loudly instead of slipping through.
    """
    registrations: list[tuple[dict, object]] = []

    def _fake_resource(**kwargs):
        def _decorator(handler):
            registrations.append((kwargs, handler))
            return handler

        return _decorator

    mcp.resource = _fake_resource
    return registrations


class TestRegisterResources:
    def test_uri_to_handler_mapping_is_correct(self):
        """Pin which handler each URI gets. A future swap (e.g. binding
        ``katana://help/tools`` to ``get_help_resources``) would silently
        misroute every Help-Tools fetch, returning the wrong document
        without any other test failing.
        """
        mcp = MagicMock()
        registrations = _capture_registrations(mcp)
        register_resources(mcp)

        uri_to_handler = {kwargs["uri"]: handler for kwargs, handler in registrations}
        assert uri_to_handler == {
            "katana://help": get_help_index,
            "katana://help/workflows": get_help_workflows,
            "katana://help/tools": get_help_tools,
            "katana://help/resources": get_help_resources,
        }

    def test_each_registration_has_a_human_name_and_description(self):
        mcp = MagicMock()
        registrations = _capture_registrations(mcp)
        register_resources(mcp)
        for kwargs, _handler in registrations:
            assert kwargs.get("name"), (
                f"Resource {kwargs['uri']} registered without a name"
            )
            assert kwargs.get("description"), (
                f"Resource {kwargs['uri']} registered without a description"
            )
