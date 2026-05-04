"""Tests for the inventory items resource (``katana://inventory/items``).

Cache-backed read of products + materials + services. Each entity type
has slightly different default-flag semantics (services default to
sellable when the field is missing/None; materials default to
purchasable; products use conservative is-True checks). The tests pin
that contract, the deleted-row filter, and the summary counts.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from katana_mcp.resources.inventory import (
    _filter_deleted,
    get_inventory_items,
    register_resources,
)

from tests.conftest import create_mock_context

ENSURE_PRODUCTS = "katana_mcp.resources.inventory.ensure_products_synced"
ENSURE_MATERIALS = "katana_mcp.resources.inventory.ensure_materials_synced"
ENSURE_SERVICES = "katana_mcp.resources.inventory.ensure_services_synced"


def _make_context_with_cache(
    *,
    products: list[dict] | None = None,
    materials: list[dict] | None = None,
    services: list[dict] | None = None,
):
    """Build a mock context whose ``cache.get_all`` returns the given
    per-entity-type buckets. The handler keys cache lookups by
    ``EntityType``; we side-effect the mock so each call returns the
    right bucket.
    """
    context, lifespan_ctx = create_mock_context()
    by_type: dict[str, list[dict]] = {
        "product": products or [],
        "material": materials or [],
        "service": services or [],
    }

    async def _get_all(entity_type):
        # EntityType is a StrEnum; ``.value`` matches the dict key
        return by_type.get(getattr(entity_type, "value", str(entity_type)), [])

    lifespan_ctx.cache.get_all = AsyncMock(side_effect=_get_all)
    return context


async def _call_and_parse(context) -> dict:
    with (
        patch(ENSURE_PRODUCTS, new_callable=AsyncMock),
        patch(ENSURE_MATERIALS, new_callable=AsyncMock),
        patch(ENSURE_SERVICES, new_callable=AsyncMock),
    ):
        result = await get_inventory_items(context)
    assert isinstance(result, str), "Resource handlers must return JSON strings"
    return json.loads(result)


# ============================================================================
# _filter_deleted helper
# ============================================================================


class TestFilterDeleted:
    def test_drops_entries_with_truthy_deleted_at(self):
        entities = [
            {"id": 1, "deleted_at": None},
            {"id": 2, "deleted_at": "2026-01-01T00:00:00Z"},
            {"id": 3, "deleted_at": ""},  # empty string falsy → keep
            {"id": 4},  # missing key → keep
        ]
        out = _filter_deleted(entities)
        assert [e["id"] for e in out] == [1, 3, 4]

    def test_empty_list_passthrough(self):
        assert _filter_deleted([]) == []


# ============================================================================
# Response shape
# ============================================================================


class TestInventoryItemsResource:
    @pytest.mark.asyncio
    async def test_empty_cache_returns_zero_summary(self):
        context = _make_context_with_cache()
        result = await _call_and_parse(context)
        assert result["summary"] == {
            "total_items": 0,
            "products": 0,
            "materials": 0,
            "services": 0,
        }
        assert result["items"] == []
        assert "generated_at" in result
        assert result["next_actions"]

    @pytest.mark.asyncio
    async def test_summary_counts_match_cache_buckets(self):
        context = _make_context_with_cache(
            products=[
                {"id": 1, "name": "Widget", "is_sellable": True},
                {"id": 2, "name": "Gear", "is_sellable": True},
            ],
            materials=[{"id": 100, "name": "Steel"}],
            services=[
                {"id": 200, "name": "Setup"},
                {"id": 201, "name": "Calibration"},
                {"id": 202, "name": "Inspection"},
            ],
        )
        result = await _call_and_parse(context)
        assert result["summary"] == {
            "total_items": 6,
            "products": 2,
            "materials": 1,
            "services": 3,
        }

    @pytest.mark.asyncio
    async def test_deleted_entities_filtered_from_each_bucket(self):
        context = _make_context_with_cache(
            products=[
                {"id": 1, "name": "Active", "deleted_at": None},
                {"id": 2, "name": "Deleted", "deleted_at": "2026-01-01T00:00:00Z"},
            ],
            materials=[
                {"id": 100, "name": "DeletedMat", "deleted_at": "2026-01-01T00:00:00Z"},
                {"id": 101, "name": "ActiveMat"},
            ],
            services=[
                {"id": 200, "name": "DeletedSvc", "deleted_at": "2026-01-01T00:00:00Z"},
            ],
        )
        result = await _call_and_parse(context)
        names = {item["name"] for item in result["items"]}
        assert names == {"Active", "ActiveMat"}
        assert result["summary"]["products"] == 1
        assert result["summary"]["materials"] == 1
        assert result["summary"]["services"] == 0


# ============================================================================
# Per-type capability defaults
# ============================================================================


class TestProductCapabilityDefaults:
    """Products: ``is_X`` flags default to False when missing/None.

    Conservative — an unset flag should not imply the product can be sold,
    produced, or purchased.
    """

    @pytest.mark.asyncio
    async def test_explicit_true_passes_through(self):
        context = _make_context_with_cache(
            products=[
                {
                    "id": 1,
                    "name": "Widget",
                    "is_sellable": True,
                    "is_producible": True,
                    "is_purchasable": True,
                }
            ]
        )
        result = await _call_and_parse(context)
        item = result["items"][0]
        assert item == {
            "id": 1,
            "name": "Widget",
            "type": "product",
            "is_sellable": True,
            "is_producible": True,
            "is_purchasable": True,
        }

    @pytest.mark.asyncio
    async def test_missing_flags_default_to_false(self):
        context = _make_context_with_cache(products=[{"id": 1, "name": "Sparse"}])
        result = await _call_and_parse(context)
        item = result["items"][0]
        assert item["is_sellable"] is False
        assert item["is_producible"] is False
        assert item["is_purchasable"] is False

    @pytest.mark.asyncio
    async def test_explicit_none_treated_as_false(self):
        context = _make_context_with_cache(
            products=[
                {
                    "id": 1,
                    "name": "Nullable",
                    "is_sellable": None,
                    "is_producible": None,
                    "is_purchasable": None,
                }
            ]
        )
        result = await _call_and_parse(context)
        item = result["items"][0]
        assert item["is_sellable"] is False
        assert item["is_producible"] is False
        assert item["is_purchasable"] is False

    @pytest.mark.asyncio
    async def test_explicit_false_stays_false(self):
        context = _make_context_with_cache(
            products=[
                {
                    "id": 1,
                    "name": "Disabled",
                    "is_sellable": False,
                    "is_producible": False,
                    "is_purchasable": False,
                }
            ]
        )
        result = await _call_and_parse(context)
        item = result["items"][0]
        assert item["is_sellable"] is False
        assert item["is_producible"] is False
        assert item["is_purchasable"] is False


class TestMaterialCapabilityDefaults:
    """Materials: always not-sellable, not-producible, purchasable.

    The handler hard-codes these flags rather than reading from cache;
    the contract is that everything in the materials bucket can be
    purchased and nothing else.
    """

    @pytest.mark.asyncio
    async def test_flags_are_constant(self):
        context = _make_context_with_cache(
            materials=[
                {
                    "id": 1,
                    "name": "Steel",
                    # These should be ignored — handler hard-codes the answer.
                    "is_sellable": True,
                    "is_producible": True,
                    "is_purchasable": False,
                }
            ]
        )
        result = await _call_and_parse(context)
        item = result["items"][0]
        assert item == {
            "id": 1,
            "name": "Steel",
            "type": "material",
            "is_sellable": False,
            "is_producible": False,
            "is_purchasable": True,
        }


class TestServiceCapabilityDefaults:
    """Services: default to sellable unless explicitly False.

    Different default direction from products — a service with no
    ``is_sellable`` field is assumed sellable (the catalog ships
    services as billable line items by default).
    """

    @pytest.mark.asyncio
    async def test_missing_flag_defaults_to_sellable(self):
        context = _make_context_with_cache(services=[{"id": 1, "name": "Setup"}])
        result = await _call_and_parse(context)
        item = result["items"][0]
        assert item["is_sellable"] is True
        assert item["is_producible"] is False
        assert item["is_purchasable"] is False

    @pytest.mark.asyncio
    async def test_explicit_none_treated_as_sellable(self):
        # Service-specific default: ``None`` is treated as sellable
        # (services were historically not-flagged in the API).
        context = _make_context_with_cache(
            services=[{"id": 1, "name": "Implicit", "is_sellable": None}]
        )
        result = await _call_and_parse(context)
        item = result["items"][0]
        assert item["is_sellable"] is True

    @pytest.mark.asyncio
    async def test_explicit_false_disables_sellable(self):
        context = _make_context_with_cache(
            services=[{"id": 1, "name": "Internal", "is_sellable": False}]
        )
        result = await _call_and_parse(context)
        item = result["items"][0]
        assert item["is_sellable"] is False

    @pytest.mark.asyncio
    async def test_explicit_true_passes_through(self):
        context = _make_context_with_cache(
            services=[{"id": 1, "name": "Billable", "is_sellable": True}]
        )
        result = await _call_and_parse(context)
        item = result["items"][0]
        assert item["is_sellable"] is True


# ============================================================================
# Cache sync invocation
# ============================================================================


class TestCacheSyncInvocation:
    """The handler must trigger an on-demand sync for every entity type
    before reading. If a sync is skipped, the cache could be stale and
    the response wouldn't reflect newly-created items.
    """

    @pytest.mark.asyncio
    async def test_all_three_syncs_run_before_cache_reads(self):
        """Pin the *order* — every sync must complete before any cache read.

        A regression that reads stale cache data first and syncs after
        would still pass an "awaited once" assertion on each mock; this
        test fails it. Tracks ordering via a shared call log appended
        from each sync's side_effect and from a wrapped ``cache.get_all``.
        """
        call_log: list[str] = []

        async def _sync_products(*_args, **_kw):
            call_log.append("sync:products")

        async def _sync_materials(*_args, **_kw):
            call_log.append("sync:materials")

        async def _sync_services(*_args, **_kw):
            call_log.append("sync:services")

        async def _cache_get_all(entity_type):
            call_log.append(f"read:{getattr(entity_type, 'value', entity_type)}")
            return []

        context, lifespan_ctx = create_mock_context()
        lifespan_ctx.cache.get_all = AsyncMock(side_effect=_cache_get_all)

        with (
            patch(ENSURE_PRODUCTS, new=AsyncMock(side_effect=_sync_products)),
            patch(ENSURE_MATERIALS, new=AsyncMock(side_effect=_sync_materials)),
            patch(ENSURE_SERVICES, new=AsyncMock(side_effect=_sync_services)),
        ):
            await get_inventory_items(context)

        # Every sync entry must appear in the log before any read entry.
        first_read_index = next(
            (i for i, entry in enumerate(call_log) if entry.startswith("read:")),
            len(call_log),
        )
        sync_entries = [e for e in call_log[:first_read_index] if e.startswith("sync:")]
        assert {"sync:products", "sync:materials", "sync:services"}.issubset(
            sync_entries
        ), f"Cache read happened before all syncs completed. Call log: {call_log}"


# ============================================================================
# Registration
# ============================================================================


def _capture_registrations(mcp) -> list[tuple[dict, object]]:
    """Wire ``mcp.resource`` to capture both the registration kwargs AND
    the handler each registration is decorated onto.

    A naive ``MagicMock(return_value=lambda fn: fn)`` only captures the
    kwargs — a swap like ``mcp.resource(uri="A")(handler_for_B)`` would
    pass any test that only asserts URI/name/description. Returns a list
    of ``(kwargs, handler)`` tuples in registration order so callers can
    pin the URI→handler mapping.
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
    def test_registers_inventory_items_with_correct_handler(self):
        from unittest.mock import MagicMock

        mcp = MagicMock()
        registrations = _capture_registrations(mcp)
        register_resources(mcp)

        assert len(registrations) == 1
        kwargs, handler = registrations[0]
        assert kwargs["uri"] == "katana://inventory/items"
        assert kwargs["mime_type"] == "application/json"
        # Pin the URI→handler mapping. A future swap (registering this
        # URI with a different handler) would silently misroute callers
        # if we only checked the kwargs.
        assert handler is get_inventory_items
