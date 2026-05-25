"""Tests for product-level BOM tooling (foundation/bom.py)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from katana_mcp.tools.foundation.bom import (
    BomRowAdd,
    BomRowUpdate,
    GetProductBomRequest,
    ManageProductBomRequest,
    _get_product_bom_impl,
    _modify_product_bom_impl,
)
from katana_mcp_server.tests.conftest import create_mock_context
from pydantic import ValidationError

from katana_public_api_client.client_types import UNSET, Unset

# ============================================================================
# Helpers
# ============================================================================


def _bom_row(
    *,
    row_id: str = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    product_item_id: int = 100,
    product_variant_id: int = 200,
    ingredient_variant_id: int = 300,
    quantity: float | Unset = 2.0,
    notes: str | Unset = UNSET,
    rank: int | Unset = 10000,
) -> MagicMock:
    """Build a generated-style ``BomRow`` MagicMock with all wire fields set."""
    row = MagicMock()
    row.id = UUID(row_id)
    row.product_item_id = product_item_id
    row.product_variant_id = product_variant_id
    row.ingredient_variant_id = ingredient_variant_id
    row.quantity = quantity
    row.notes = notes
    row.rank = rank
    return row


def _mock_variant(
    *,
    id: int,
    sku: str | None,
    display_name: str | None = None,
    product_id: int | None = None,
    material_id: int | None = None,
) -> MagicMock:
    v = MagicMock()
    v.id = id
    v.sku = sku
    v.display_name = display_name or (sku or f"variant-{id}")
    v.product_id = product_id
    v.material_id = material_id
    return v


# ============================================================================
# get_product_bom
# ============================================================================


@pytest.mark.asyncio
async def test_get_product_bom_returns_rows_with_resolved_ingredient_sku():
    """The BOM read path enriches each row with the cached ingredient SKU
    and display_name — the same pattern as ``RecipeRowInfo`` for MO recipes.
    The Spot Bikes case: SP0502 bundle made from SK74001 + SK74003."""
    context, lifespan = create_mock_context()
    rows = [
        _bom_row(
            row_id="11111111-1111-1111-1111-111111111111",
            ingredient_variant_id=301,
            quantity=2.0,
        ),
        _bom_row(
            row_id="22222222-2222-2222-2222-222222222222",
            ingredient_variant_id=302,
            quantity=2.0,
        ),
    ]
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            301: _mock_variant(
                id=301, sku="SK74001", display_name="Industry Nine 295mm"
            ),
            302: _mock_variant(
                id=302, sku="SK74003", display_name="Industry Nine 299mm"
            ),
        }
    )

    with patch(
        "katana_mcp.tools.foundation.bom._fetch_bom_rows",
        new_callable=AsyncMock,
        return_value=rows,
    ):
        response = await _get_product_bom_impl(
            GetProductBomRequest(product_variant_id=200), context
        )

    assert response.product_variant_id == 200
    assert response.total_count == 2
    assert response.rows[0].sku == "SK74001"
    assert response.rows[0].display_name == "Industry Nine 295mm"
    assert response.rows[0].quantity == 2.0
    assert response.rows[1].sku == "SK74003"
    # Row id is stringified UUID so the wire shape is plain text.
    assert response.rows[0].id == "11111111-1111-1111-1111-111111111111"


@pytest.mark.asyncio
async def test_get_product_bom_empty_recipe_returns_zero_rows():
    """A variant with no recipe gets a clean empty response, not an error."""
    context, _ = create_mock_context()
    with patch(
        "katana_mcp.tools.foundation.bom._fetch_bom_rows",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response = await _get_product_bom_impl(
            GetProductBomRequest(product_variant_id=200), context
        )

    assert response.total_count == 0
    assert response.rows == []


@pytest.mark.asyncio
async def test_get_product_bom_populates_parent_for_card():
    """The response carries parent product + variant display info so the
    Prefab card's Tier-1 header has a name to render (#810 fix). Walks
    ``_resolve_parent_for_card``: variant cache lookup → product cache
    lookup → fields populated.
    """
    context, lifespan = create_mock_context()

    # Variant cache hit — points at product_id 9001.
    variant = _mock_variant(
        id=200,
        sku="FRAME-A",
        display_name="Test Frame / Standard",
        product_id=9001,
    )
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={200: variant}
    )

    # Product cache hit — supplies name, is_producible, uom.
    product = MagicMock()
    product.id = 9001
    product.name = "Test Frame"
    product.is_producible = True
    product.uom = "pcs"
    lifespan.typed_cache.catalog.get_by_id = AsyncMock(return_value=product)

    with patch(
        "katana_mcp.tools.foundation.bom._fetch_bom_rows",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response = await _get_product_bom_impl(
            GetProductBomRequest(product_variant_id=200), context
        )

    assert response.product_id == 9001
    assert response.product_name == "Test Frame"
    assert response.variant_sku == "FRAME-A"
    assert response.variant_display_name == "Test Frame / Standard"
    assert response.is_producible is True
    assert response.uom == "pcs"
    assert response.katana_url is not None
    assert "9001" in response.katana_url


@pytest.mark.asyncio
async def test_get_product_bom_card_fields_fall_back_to_none_on_cache_miss():
    """A cold cache (no variant or product hit) falls through cleanly —
    response still builds, card-display fields are None, rows are
    untouched. Best-effort: the read path must not raise on cache miss.
    """
    context, lifespan = create_mock_context()
    # Empty get_many_by_ids → variant cache miss → product never fetched.
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    with patch(
        "katana_mcp.tools.foundation.bom._fetch_bom_rows",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response = await _get_product_bom_impl(
            GetProductBomRequest(product_variant_id=200), context
        )

    assert response.product_variant_id == 200
    assert response.product_id is None
    assert response.product_name is None
    assert response.variant_sku is None
    assert response.is_producible is None
    assert response.katana_url is None


@pytest.mark.asyncio
async def test_get_product_bom_uncached_ingredient_yields_null_sku():
    """When a referenced ingredient variant isn't in the cache, the row
    still surfaces — sku and display_name fall back to None rather than
    blocking the read."""
    context, lifespan = create_mock_context()
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    with patch(
        "katana_mcp.tools.foundation.bom._fetch_bom_rows",
        new_callable=AsyncMock,
        return_value=[_bom_row(ingredient_variant_id=999)],
    ):
        response = await _get_product_bom_impl(
            GetProductBomRequest(product_variant_id=200), context
        )

    assert response.rows[0].sku is None
    assert response.rows[0].display_name is None
    assert response.rows[0].ingredient_variant_id == 999


# ============================================================================
# manage_product_bom — entry-condition checks
# ============================================================================


@pytest.mark.asyncio
async def test_manage_bom_rejects_empty_request():
    """A request with no sub-payloads is a no-op and should error fast."""
    context, _ = create_mock_context()
    with pytest.raises(ValueError, match="At least one sub-payload"):
        await _modify_product_bom_impl(
            ManageProductBomRequest(id=200, preview=True), context
        )


@pytest.mark.asyncio
async def test_manage_bom_rejects_uncached_variant_on_add():
    """Adds require the parent product/material id; if the variant can't be
    resolved the tool errors with a clear message instead of letting the
    API return a generic 422."""
    context, lifespan = create_mock_context()
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    with pytest.raises(ValueError, match="not found in catalog"):
        await _modify_product_bom_impl(
            ManageProductBomRequest(
                id=200,
                add_bom_rows=[BomRowAdd(ingredient_variant_id=301, quantity=2.0)],
                preview=True,
            ),
            context,
        )


@pytest.mark.asyncio
async def test_manage_bom_rejects_variant_with_no_parent():
    """A variant cached but with neither product_id nor material_id is an
    orphan — BOM rows require a parent, so the tool refuses."""
    context, lifespan = create_mock_context()
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            200: _mock_variant(id=200, sku="ORPHAN"),
        }
    )

    with pytest.raises(ValueError, match="neither a parent product nor material"):
        await _modify_product_bom_impl(
            ManageProductBomRequest(
                id=200,
                add_bom_rows=[BomRowAdd(ingredient_variant_id=301, quantity=2.0)],
                preview=True,
            ),
            context,
        )


# ============================================================================
# manage_product_bom — preview/apply
# ============================================================================


@pytest.mark.asyncio
async def test_manage_bom_preview_emits_planned_actions_without_http():
    """Preview mode emits the per-action plan but does not hit the API."""
    context, lifespan = create_mock_context()
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            200: _mock_variant(id=200, sku="SP0502", product_id=17092695),
        }
    )

    with patch(
        "katana_mcp.tools.foundation.bom._fetch_bom_row_infos",
        new_callable=AsyncMock,
        return_value=[],
    ):
        request = ManageProductBomRequest(
            id=200,
            add_bom_rows=[
                BomRowAdd(ingredient_variant_id=301, quantity=2.0),
                BomRowAdd(ingredient_variant_id=302, quantity=2.0),
            ],
            delete_bom_row_ids=[UUID("11111111-1111-1111-1111-111111111111")],
            preview=True,
        )
        response = await _modify_product_bom_impl(request, context)

    assert response.is_preview is True
    assert response.entity_id == 200
    # Two adds + one delete = 3 planned actions.
    assert len(response.actions) == 3
    assert response.actions[0].operation == "add_bom_row"
    assert response.actions[2].operation == "delete_bom_row"
    # Delete target is the UUID stringified.
    assert response.actions[2].target_id == "11111111-1111-1111-1111-111111111111"
    assert all(a.succeeded is None for a in response.actions)
    # entity_type carries the parent semantic, not the row semantic.
    assert response.entity_type == "product_bom"


@pytest.mark.asyncio
async def test_manage_bom_apply_populates_prior_state_from_snapshot():
    """The dispatcher's ``prior_state`` is populated from the BOM snapshot
    fetched at the top of ``_modify_product_bom_impl`` — this gives callers
    a manual-revert record even when the plan partially applies (fail-fast).
    """
    from katana_mcp.tools.foundation.bom import BomRowInfo

    context, lifespan = create_mock_context()
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    existing_rows = [
        BomRowInfo(
            id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            product_item_id=17092695,
            product_variant_id=200,
            ingredient_variant_id=301,
            sku="SK74001",
            quantity=2.0,
        )
    ]

    async def fake_delete(*, id, client):
        resp = MagicMock()
        resp.status_code = 204
        return resp

    with (
        patch(
            "katana_mcp.tools.foundation.bom._fetch_bom_row_infos",
            new_callable=AsyncMock,
            return_value=existing_rows,
        ),
        patch(
            "katana_mcp.tools.foundation.bom.api_delete_bom_row.asyncio_detailed",
            side_effect=fake_delete,
        ),
        patch(
            "katana_mcp.tools.foundation.bom.is_success",
            return_value=True,
        ),
    ):
        request = ManageProductBomRequest(
            id=200,
            delete_bom_row_ids=[UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")],
            preview=False,
        )
        response = await _modify_product_bom_impl(request, context)

    assert response.is_preview is False
    assert response.prior_state is not None
    assert response.prior_state["total_count"] == 1
    assert response.prior_state["rows"][0]["sku"] == "SK74001"


@pytest.mark.asyncio
async def test_manage_bom_response_carries_resolved_ingredients_for_renderer():
    """#811: the BOM modify card needs ingredient SKU + display_name for
    rows that *don't* have the identity inline on the snapshot.

    Renderer contract (per ``_merge_bom_rows_for_modify_card``):
    - **Existing / deleted rows** — read SKU / display_name directly off
      the snapshot row dict. The snapshot already resolved them via
      ``_fetch_bom_row_infos`` so no further lookup is needed.
    - **Added rows** — synthesized from the ``add_bom_row`` action's
      ``changes``; the new ingredient_variant_id has no snapshot row to
      reference, so the SKU / display_name come from
      ``resolved_ingredients[ingredient_id]``.
    - **Updated rows with an ingredient swap** — the post-patch identity
      replaces the snapshot identity, again sourced from
      ``resolved_ingredients`` for the swapped-in variant id.

    The impl (see :func:`_collect_ingredient_ids`) batches a single
    cache lookup across the targeted union: every add's target ingredient,
    every update's NEW ingredient when swap-shaped, plus every
    update / delete TARGET row's existing ingredient (resolved via the
    snapshot so the renderer can render the pre-patch identity). Rows
    that aren't touched by the plan don't contribute — their identity
    is already in the snapshot's ``rows[*].sku`` / ``display_name``.
    This test pins that union: one add + one update + one delete →
    those three ingredient_variant_ids are in the map.
    """
    from katana_mcp.tools.foundation.bom import BomRowInfo

    context, lifespan = create_mock_context()
    existing_rows = [
        BomRowInfo(
            id="11111111-1111-1111-1111-111111111111",
            product_item_id=100,
            product_variant_id=200,
            ingredient_variant_id=401,  # gets updated
            sku="BLT-M5-10",
            quantity=6.0,
        ),
        BomRowInfo(
            id="22222222-2222-2222-2222-222222222222",
            product_item_id=100,
            product_variant_id=200,
            ingredient_variant_id=402,  # gets deleted
            sku="BLT-M6-12",
            quantity=4.0,
        ),
    ]

    def _resolve(model, variant_ids, **kwargs):
        return {
            vid: _mock_variant(id=vid, sku=f"SKU-{vid}", product_id=100)
            for vid in variant_ids
        }

    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_resolve)

    with patch(
        "katana_mcp.tools.foundation.bom._fetch_bom_row_infos",
        new_callable=AsyncMock,
        return_value=existing_rows,
    ):
        request = ManageProductBomRequest(
            id=200,
            add_bom_rows=[BomRowAdd(ingredient_variant_id=301, quantity=2.0)],
            update_bom_rows=[
                BomRowUpdate(
                    id=UUID("11111111-1111-1111-1111-111111111111"),
                    quantity=8.0,
                )
            ],
            delete_bom_row_ids=[UUID("22222222-2222-2222-2222-222222222222")],
            preview=True,
        )
        response = await _modify_product_bom_impl(request, context)

    resolved = response.extras.get("resolved_ingredients")
    assert isinstance(resolved, dict)
    # Every ingredient_variant_id from add + delete + update target's
    # existing row appears in the resolved map. (Updates that don't swap
    # the ingredient still need the existing row's id resolved so the
    # row identity surfaces in the card.)
    assert 301 in resolved  # add
    assert 401 in resolved  # update target's existing ingredient
    assert 402 in resolved  # delete target's existing ingredient
    # Resolved entries carry the typed sku/display_name shape the
    # renderer reads.
    assert resolved[301]["sku"] == "SKU-301"
    # Preview response: applied_plan_rows NOT populated (computed only
    # on the apply branch). The iframe seeds state.plan_rows from the
    # preview table_rows at first render; applied_plan_rows is reserved
    # for the on_success SetState morph.
    assert "applied_plan_rows" not in response.extras


@pytest.mark.asyncio
async def test_manage_bom_apply_response_carries_applied_plan_rows():
    """#811 follow-up: the apply response must precompute the
    resolved-status table rows so the iframe's Confirm chain can
    SetState the DataTable bindings to the actual outcome (APPLIED /
    FAILED) instead of leaving the seeded preview rows stuck on
    PLANNED. Reads from ``response.extras["applied_plan_rows"]``;
    each row carries the merged-row shape (kind / status_prefix /
    sku_label / status_label / etc.) — i.e. the same row dicts
    ``_prepare_bom_table_rows`` produces.
    """
    from katana_mcp.tools.foundation.bom import BomRowInfo

    context, lifespan = create_mock_context()
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            200: _mock_variant(id=200, sku="SP0502", product_id=17092695),
        }
    )

    async def fake_create(*, client, body):
        resp = MagicMock()
        resp.status_code = 204
        resp.parsed = None
        return resp

    existing_rows = [
        BomRowInfo(
            id="11111111-1111-1111-1111-111111111111",
            product_item_id=100,
            product_variant_id=200,
            ingredient_variant_id=401,
            sku="BLT-M5-10",
            quantity=6.0,
        ),
    ]

    with (
        patch(
            "katana_mcp.tools.foundation.bom._fetch_bom_row_infos",
            new_callable=AsyncMock,
            return_value=existing_rows,
        ),
        patch(
            "katana_mcp.tools.foundation.bom.api_create_bom_row.asyncio_detailed",
            side_effect=fake_create,
        ),
    ):
        request = ManageProductBomRequest(
            id=200,
            add_bom_rows=[BomRowAdd(ingredient_variant_id=301, quantity=2.0)],
            preview=False,
        )
        response = await _modify_product_bom_impl(request, context)

    assert response.is_preview is False
    applied_rows = response.extras.get("applied_plan_rows")
    assert isinstance(applied_rows, list)
    # One existing row (untouched) + one added row.
    assert len(applied_rows) == 2
    # The added row reflects the resolved status (APPLIED) — not the
    # PLANNED-stuck-on-preview state. ``_prepare_bom_table_rows`` glues
    # the kind-prefix gutter onto sku_label.
    added = next(r for r in applied_rows if r["kind"] == "added")
    assert added["status_label"] == "APPLIED"
    assert added["status_prefix"] == "+ "
    # The existing untouched row stays as such — applied_plan_rows
    # carries the FULL post-merge table, not just the planned actions.
    untouched = next(r for r in applied_rows if r["kind"] == "existing")
    assert untouched["sku"] == "BLT-M5-10"


@pytest.mark.asyncio
async def test_manage_bom_apply_synthesizes_not_run_for_fail_fast_tail():
    """``execute_plan`` is fail-fast: ``response.actions`` ends at the
    first failed action. The impl must synthesize NOT RUN entries for
    plan tail entries that were never attempted, otherwise the morphed
    DataTable would silently hide them — the operator sees "1 added"
    when the plan was actually "1 added, 2 never-attempted".

    Pins ``applied_plan_rows`` includes the never-run entries with
    ``status_label="NOT RUN"`` and ``applied_failed_summary`` calls
    out the count.
    """
    context, lifespan = create_mock_context()
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            200: _mock_variant(id=200, sku="SP0502", product_id=17092695),
        }
    )

    call_count = {"n": 0}

    async def fake_create(*, client, body):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # First add fails — execute_plan halts here.
            raise RuntimeError("422 ingredient_variant_id is required")
        # Should never be reached because fail-fast halts after the first.
        resp = MagicMock()
        resp.status_code = 204
        resp.parsed = None
        return resp

    with (
        patch(
            "katana_mcp.tools.foundation.bom._fetch_bom_row_infos",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "katana_mcp.tools.foundation.bom.api_create_bom_row.asyncio_detailed",
            side_effect=fake_create,
        ),
    ):
        request = ManageProductBomRequest(
            id=200,
            add_bom_rows=[
                BomRowAdd(ingredient_variant_id=301, quantity=1.0),
                BomRowAdd(ingredient_variant_id=302, quantity=1.0),
                BomRowAdd(ingredient_variant_id=303, quantity=1.0),
            ],
            preview=False,
        )
        response = await _modify_product_bom_impl(request, context)

    # Only the first action was attempted (and failed); the rest were
    # never run.
    assert call_count["n"] == 1
    assert len(response.actions) == 1
    assert response.actions[0].succeeded is False

    applied_rows = response.extras.get("applied_plan_rows")
    assert isinstance(applied_rows, list)
    # 3 added rows (one FAILED, two NOT RUN). Existing snapshot was empty.
    assert len(applied_rows) == 3
    statuses = [r.get("status_label") for r in applied_rows]
    assert statuses.count("FAILED") == 1
    assert statuses.count("NOT RUN") == 2
    # The summary tells the operator how to recover.
    assert "NOT RUN" in response.extras.get("applied_failed_summary", "")
    assert "re-issue manage_product_bom" in response.extras.get(
        "applied_failed_summary", ""
    )


@pytest.mark.asyncio
async def test_manage_bom_apply_calls_create_for_each_add():
    """Confirm mode executes per-action POST /bom_rows for each add.

    Katana's ``POST /bom_rows`` returns 204 No Content — no body. The
    apply closure (post-#809) confirms 2xx via ``is_success`` and does
    not try to parse a row. The mock response carries ``status_code=204``
    so ``is_success`` returns True without touching ``response.parsed``.
    """
    context, lifespan = create_mock_context()
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            200: _mock_variant(id=200, sku="SP0502", product_id=17092695),
        }
    )

    captured_bodies: list = []

    async def fake_create(*, client, body):
        captured_bodies.append(body)
        resp = MagicMock()
        resp.status_code = 204
        resp.parsed = None
        return resp

    with (
        patch(
            "katana_mcp.tools.foundation.bom._fetch_bom_row_infos",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "katana_mcp.tools.foundation.bom.api_create_bom_row.asyncio_detailed",
            side_effect=fake_create,
        ),
    ):
        request = ManageProductBomRequest(
            id=200,
            add_bom_rows=[
                BomRowAdd(ingredient_variant_id=301, quantity=2.0),
                BomRowAdd(ingredient_variant_id=302, quantity=2.0),
            ],
            preview=False,
        )
        response = await _modify_product_bom_impl(request, context)

    assert response.is_preview is False
    assert all(a.succeeded is True for a in response.actions)
    assert len(captured_bodies) == 2
    # Each create body carries the parent ids resolved from the cached variant.
    assert captured_bodies[0].product_item_id == 17092695
    assert captured_bodies[0].product_variant_id == 200
    assert captured_bodies[0].ingredient_variant_id == 301
    assert captured_bodies[1].ingredient_variant_id == 302


@pytest.mark.asyncio
async def test_manage_bom_apply_commits_all_rows_against_204_transport():
    """Regression for #809: ``POST /bom_rows`` returns 204 No Content per the
    Katana spec. The generated ``_parse_response`` matches the 204 branch,
    sets ``response.parsed = None``, and the previous ``unwrap_as(response,
    BomRow)`` then raised ``APIError`` because ``unwrap`` treated
    ``parsed is None`` as an error regardless of status. Fail-fast halted
    the plan after the first row, so a 30-row batch silently became a
    1-row commit in Katana.

    This test drives a real :class:`KatanaClient` against an ``httpx.MockTransport``
    that returns 204 on every POST — exactly mirroring production — and
    asserts all rows in the batch run.
    """
    import httpx

    from katana_public_api_client import KatanaClient

    posts_served: list[bytes] = []

    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path.endswith("/bom_rows") and req.method == "POST":
            posts_served.append(req.content)
            return httpx.Response(204)
        return httpx.Response(404, json={"error": "unexpected route"})

    async with KatanaClient(
        api_key="test-key",
        base_url="https://api.example.com",
        transport=httpx.MockTransport(handler),
    ) as client:
        context, lifespan = create_mock_context()
        lifespan.client = client
        lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(
            return_value={
                200: _mock_variant(id=200, sku="SP0502", product_id=17092695),
            }
        )

        with patch(
            "katana_mcp.tools.foundation.bom._fetch_bom_row_infos",
            new_callable=AsyncMock,
            return_value=[],
        ):
            request = ManageProductBomRequest(
                id=200,
                add_bom_rows=[
                    BomRowAdd(ingredient_variant_id=300 + i, quantity=1.0)
                    for i in range(5)
                ],
                preview=False,
            )
            response = await _modify_product_bom_impl(request, context)

    assert len(posts_served) == 5, (
        f"Only {len(posts_served)} of 5 POSTs reached Katana — "
        "apply loop halted after the first row (regression of #809)."
    )
    assert len(response.actions) == 5
    assert all(a.succeeded is True for a in response.actions), (
        f"Some actions failed: {[(a.operation, a.error) for a in response.actions]}"
    )


@pytest.mark.asyncio
async def test_manage_bom_apply_calls_update_then_delete():
    """Updates use PATCH /bom_rows/{uuid}; deletes use DELETE /bom_rows/{uuid}.
    Both must accept UUID — confirmed indirectly by ``asyncio_detailed``
    accepting the patched UUID without coercion."""
    context, _ = create_mock_context()

    updated_row = _bom_row(notes="updated")
    update_calls: list = []
    delete_calls: list = []

    async def fake_update(*, id, client, body):
        update_calls.append((id, body))
        resp = MagicMock()
        resp.parsed = updated_row
        return resp

    async def fake_delete(*, id, client):
        delete_calls.append(id)
        resp = MagicMock()
        resp.status_code = 204
        return resp

    row_uuid_a = UUID("11111111-1111-1111-1111-111111111111")
    row_uuid_b = UUID("22222222-2222-2222-2222-222222222222")

    with (
        patch(
            "katana_mcp.tools.foundation.bom._fetch_bom_row_infos",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "katana_mcp.tools.foundation.bom.api_update_bom_row.asyncio_detailed",
            side_effect=fake_update,
        ),
        patch(
            "katana_mcp.tools.foundation.bom.api_delete_bom_row.asyncio_detailed",
            side_effect=fake_delete,
        ),
        patch(
            "katana_mcp.tools.foundation.bom.unwrap_as",
            return_value=updated_row,
        ),
        patch(
            "katana_mcp.tools.foundation.bom.is_success",
            return_value=True,
        ),
    ):
        request = ManageProductBomRequest(
            id=200,
            update_bom_rows=[BomRowUpdate(id=row_uuid_a, quantity=3.0)],
            delete_bom_row_ids=[row_uuid_b],
            preview=False,
        )
        response = await _modify_product_bom_impl(request, context)

    assert response.is_preview is False
    assert all(a.succeeded is True for a in response.actions)
    assert update_calls == [(row_uuid_a, update_calls[0][1])]
    assert delete_calls == [row_uuid_b]


@pytest.mark.asyncio
async def test_manage_bom_update_diff_marked_unknown_prior():
    """BOM rows have no individual GET-by-id endpoint, so every update diff
    is marked ``is_unknown_prior=True``. Renderers downstream rely on this
    flag to avoid implying a prior value we don't actually know."""
    context, _ = create_mock_context()

    request = ManageProductBomRequest(
        id=200,
        update_bom_rows=[
            BomRowUpdate(id=UUID("11111111-1111-1111-1111-111111111111"), quantity=3.0)
        ],
        preview=True,
    )
    response = await _modify_product_bom_impl(request, context)

    update_action = response.actions[0]
    assert update_action.operation == "update_bom_row"
    assert update_action.changes  # diff has at least one change
    assert all(c.is_unknown_prior for c in update_action.changes)


@pytest.mark.asyncio
async def test_manage_bom_apply_falls_through_on_create_failure():
    """Fail-fast: a failed create halts the plan; later actions don't run."""
    context, lifespan = create_mock_context()
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            200: _mock_variant(id=200, sku="SP0502", product_id=17092695),
        }
    )

    async def fake_create_fails(*, client, body):
        raise RuntimeError("Katana 422: duplicate ingredient")

    with patch(
        "katana_mcp.tools.foundation.bom.api_create_bom_row.asyncio_detailed",
        side_effect=fake_create_fails,
    ):
        request = ManageProductBomRequest(
            id=200,
            add_bom_rows=[
                BomRowAdd(ingredient_variant_id=301, quantity=2.0),
                BomRowAdd(ingredient_variant_id=302, quantity=2.0),
            ],
            preview=False,
        )
        response = await _modify_product_bom_impl(request, context)

    # Only the first action's result is recorded; the second is dropped
    # by fail-fast.
    assert len(response.actions) == 1
    assert response.actions[0].succeeded is False
    assert "duplicate" in (response.actions[0].error or "")


# ============================================================================
# Request validation
# ============================================================================


def test_bom_row_update_rejects_extra_fields():
    """``extra="forbid"`` on patch models catches typos like
    ``ingredient_id`` (vs the correct ``ingredient_variant_id``)."""
    with pytest.raises(ValidationError):
        BomRowUpdate.model_validate(
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "ingredient_id": 999,
            }
        )


def test_bom_row_add_rejects_negative_quantity():
    """``ge=0`` keeps malformed quantity out of the API."""
    with pytest.raises(ValidationError):
        BomRowAdd.model_validate({"ingredient_variant_id": 301, "quantity": -1})


def test_bom_row_update_rejects_id_only_patch():
    """A patch with only ``id`` set has no patchable fields — would yield
    an empty PATCH body and a generic 422. The validator catches it at
    the request boundary before any plan is built."""
    with pytest.raises(ValidationError, match="at least one of"):
        BomRowUpdate.model_validate({"id": "11111111-1111-1111-1111-111111111111"})


# ============================================================================
# Round-trip serialization
# ============================================================================


@pytest.mark.asyncio
async def test_get_product_bom_response_is_json_serializable():
    """The response model must roundtrip cleanly to JSON — UUIDs render as
    strings, no datetime hiccups."""
    context, lifespan = create_mock_context()
    lifespan.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            301: _mock_variant(id=301, sku="SK74001"),
        }
    )
    with patch(
        "katana_mcp.tools.foundation.bom._fetch_bom_rows",
        new_callable=AsyncMock,
        return_value=[_bom_row(ingredient_variant_id=301)],
    ):
        response = await _get_product_bom_impl(
            GetProductBomRequest(product_variant_id=200), context
        )

    payload = json.loads(response.model_dump_json())
    assert payload["product_variant_id"] == 200
    assert payload["rows"][0]["sku"] == "SK74001"
    assert payload["rows"][0]["id"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
