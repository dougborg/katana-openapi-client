"""Tests for the exhaustive get_variant_details / get_item path.

Scope: #346 items slice — pins the full-field-coverage contract and the
canonical-name markdown rendering so a future refactor can't silently drop
Variant / Product / Material / Service fields or revert to prettified
headers that LLM consumers misread (the SW7083 supplier_item_codes bug).
"""

from __future__ import annotations

import json
from typing import cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.items import (
    GetItemRequest,
    GetVariantDetailsRequest,
    ItemType,
    VariantNotFound,
    _get_item_impl,
    _get_variant_details_impl,
    get_item,
    get_variant_details,
)
from katana_mcp_server.tests.conftest import (
    create_mock_context,
    mock_item as _mock_item,
)
from pydantic import ValidationError


def _content_text(result) -> str:
    """Extract the text of a ToolResult's first content block."""
    return result.content[0].text


# ============================================================================
# Shared patches — cache_sync decorator + API fetch helper
# ============================================================================


@pytest.fixture(autouse=True)
def _patch_cache_sync():
    """Patch entity syncs for all unit tests.

    The @cache_read decorator caches sync functions in a module-level dict on
    first call, so patching the cache_sync module alone is not enough — we
    also need to clear and re-mock the cached mapping in the decorators module.

    ``get_variant_details`` syncs Variant plus Product, Material, and Supplier
    (so the parent-derived ``default_supplier_id`` / ``default_supplier_name``
    can be lifted onto the variant response — see #613-followup), so all four
    are mocked.

    Decorator keys are now typed-cache ``Cached*`` classes (#472 Phase C).
    """
    from katana_mcp.tools import decorators

    from katana_public_api_client.models_pydantic._generated import (
        CachedMaterial,
        CachedProduct,
        CachedSupplier,
        CachedVariant,
    )

    original = decorators._sync_fns
    decorators._sync_fns = {
        CachedVariant: AsyncMock(),
        CachedProduct: AsyncMock(),
        CachedMaterial: AsyncMock(),
        CachedSupplier: AsyncMock(),
    }
    try:
        yield
    finally:
        decorators._sync_fns = original


# ============================================================================
# get_variant_details — full field coverage
# ============================================================================


_FULL_VARIANT_DICT = {
    "id": 3001,
    "sku": "KNF-PRO-8PC-STL",
    "display_name": "Professional Kitchen Knife Set / 8-piece / Steel",
    "parent_name": "Professional Kitchen Knife Set",
    "type": "product",
    "product_id": 101,
    "material_id": None,
    "sales_price": 299.99,
    "purchase_price": 150.0,
    "internal_barcode": "INT-KNF-001",
    "registered_barcode": "789123456789",
    "supplier_item_codes": ["SUP-KNF-8PC-001"],
    "lead_time": 7,
    "minimum_order_quantity": 1,
    "config_attributes": [
        {"config_name": "Piece Count", "config_value": "8-piece"},
        {"config_name": "Handle Material", "config_value": "Steel"},
    ],
    "custom_fields": [
        {"field_name": "Warranty Period", "field_value": "5 years"},
    ],
    "created_at": "2024-01-15T08:00:00+00:00",
    "updated_at": "2024-08-20T14:45:00+00:00",
    "deleted_at": None,
}


@pytest.mark.asyncio
async def test_get_variant_details_surfaces_every_variant_field():
    """Every field on the generated Variant attrs model surfaces through
    VariantDetailsResponse. The #346 audit identified `deleted_at` as the
    primary gap — pin it here alongside the pre-existing fields so a future
    refactor can't silently drop either."""
    context, lifespan_ctx = create_mock_context()
    variant_dict = dict(_FULL_VARIANT_DICT)
    # Populate deleted_at to confirm it's surfaced (not just initialized).
    variant_dict["deleted_at"] = "2024-09-01T12:00:00+00:00"

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=variant_dict)

    request = GetVariantDetailsRequest(sku="KNF-PRO-8PC-STL")
    result_envelope = await _get_variant_details_impl(request, context)
    result = result_envelope.found[0]

    # Core fields
    assert result.id == 3001
    assert result.sku == "KNF-PRO-8PC-STL"
    # Pricing
    assert result.sales_price == 299.99
    assert result.purchase_price == 150.0
    # Classification
    assert result.type == "product"
    assert result.product_id == 101
    assert result.material_id is None
    assert result.product_or_material_name == "Professional Kitchen Knife Set"
    # Barcodes + supplier codes
    assert result.internal_barcode == "INT-KNF-001"
    assert result.registered_barcode == "789123456789"
    assert result.supplier_item_codes == ["SUP-KNF-8PC-001"]
    # Ordering
    assert result.lead_time == 7
    assert result.minimum_order_quantity == 1
    # Nested
    assert len(result.config_attributes) == 2
    assert len(result.custom_fields) == 1
    # Timestamps — deleted_at is the pre-#346 gap:
    assert result.created_at == "2024-01-15T08:00:00+00:00"
    assert result.updated_at == "2024-08-20T14:45:00+00:00"
    assert result.deleted_at == "2024-09-01T12:00:00+00:00"


@pytest.mark.asyncio
async def test_get_variant_details_content_includes_deleted_at():
    """JSON content round-trips ``deleted_at`` (the pre-#346 drop). Every
    request shape — single or batch — returns the ``{variants, not_found}``
    envelope so callers see one stable contract (#567 PR #719 review)."""
    context, lifespan_ctx = create_mock_context()
    variant = dict(_FULL_VARIANT_DICT)
    variant["deleted_at"] = "2024-09-01T12:00:00+00:00"
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=variant)

    result = await get_variant_details(sku="KNF-PRO-8PC-STL", context=context)

    data = json.loads(_content_text(result))
    assert data["variants"][0]["deleted_at"] == "2024-09-01T12:00:00+00:00"
    assert data["not_found"] == []


@pytest.mark.asyncio
async def test_get_variant_details_syncs_parent_entity_caches():
    """get_variant_details lifts ``default_supplier_id`` / ``_name`` from the
    parent product/material — so Product, Material, and Supplier caches must
    be synced alongside Variant before the lookup runs. Otherwise a fresh
    install / cold cache yields ``default_supplier_id: null`` for variants
    whose parent simply hasn't been cached yet.
    """
    from katana_mcp.tools import decorators

    from katana_public_api_client.models_pydantic._generated import (
        CachedMaterial,
        CachedProduct,
        CachedSupplier,
        CachedVariant,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value=dict(_FULL_VARIANT_DICT)
    )

    request = GetVariantDetailsRequest(sku="KNF-PRO-8PC-STL")
    await _get_variant_details_impl(request, context)

    sync_fns = decorators._sync_fns
    assert sync_fns is not None  # set by the autouse fixture
    for cls in (
        CachedVariant,
        CachedProduct,
        CachedMaterial,
        CachedSupplier,
    ):
        # Fixture stores AsyncMock instances; the dict's declared element
        # type is the production callable signature, so cast for ty.
        cast("AsyncMock", sync_fns[cls]).assert_awaited()


@pytest.mark.asyncio
async def test_get_variant_details_lifts_default_supplier_from_parent():
    """When parent + supplier are present in the cache, ``default_supplier_id``
    and ``default_supplier_name`` are lifted onto the variant response
    (regression: cold-cache call previously returned ``null`` because
    PRODUCT/SUPPLIER were never synced before the parent lookup).
    """
    context, lifespan_ctx = create_mock_context()
    variant = dict(_FULL_VARIANT_DICT)
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=variant)

    parent_product = {
        "id": 101,
        "uom": "set",
        "default_supplier_id": 555,
        "batch_tracked": False,
    }
    supplier = {"id": 555, "name": "Acme Cutlery Co"}

    async def _get_many_by_ids(entity_type, ids, **_kw):
        from katana_public_api_client.models_pydantic._generated import (
            CachedProduct,
            CachedSupplier,
        )

        if entity_type == CachedProduct:
            return {101: parent_product} if 101 in set(ids) else {}
        if entity_type == CachedSupplier:
            return {555: supplier} if 555 in set(ids) else {}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        side_effect=_get_many_by_ids
    )

    request = GetVariantDetailsRequest(sku="KNF-PRO-8PC-STL")
    [result] = (await _get_variant_details_impl(request, context)).found

    assert result.default_supplier_id == 555
    assert result.default_supplier_name == "Acme Cutlery Co"
    assert result.uom == "set"
    assert result.is_batch_tracked is False


@pytest.mark.asyncio
async def test_get_variant_details_lifts_purchase_uom_from_parent():
    """``purchase_uom`` and ``purchase_uom_conversion_rate`` live on the parent
    product/material (item-header fields), not on the variant attrs model.
    ``_dict_to_variant_details`` must lift them through so a single
    ``get_variant_details`` call carries enough context to draft an accurate
    PO without a follow-up parent lookup.
    """
    context, lifespan_ctx = create_mock_context()
    variant = dict(_FULL_VARIANT_DICT)
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=variant)

    parent_product = {
        "id": 101,
        "uom": "pcs",
        "purchase_uom": "kit",
        "purchase_uom_conversion_rate": 4.0,
        "default_supplier_id": 555,
        "batch_tracked": False,
    }
    supplier = {"id": 555, "name": "Industry Nine"}

    async def _get_many_by_ids(entity_type, ids, **_kw):
        from katana_public_api_client.models_pydantic._generated import (
            CachedProduct,
            CachedSupplier,
        )

        if entity_type == CachedProduct:
            return {101: parent_product} if 101 in set(ids) else {}
        if entity_type == CachedSupplier:
            return {555: supplier} if 555 in set(ids) else {}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        side_effect=_get_many_by_ids
    )

    request = GetVariantDetailsRequest(sku="KNF-PRO-8PC-STL")
    [result] = (await _get_variant_details_impl(request, context)).found

    assert result.uom == "pcs"
    assert result.purchase_uom == "kit"
    assert result.purchase_uom_conversion_rate == 4.0


@pytest.mark.asyncio
async def test_get_variant_details_api_fallback_derives_display_name_and_parent_name():
    """API-fallback path (variant absent from cache, fetched fresh from
    ``GET /variants/{id}``) still produces a complete response.

    The raw ``Variant`` attrs model has neither ``display_name`` nor
    ``parent_name`` — those are cache-only synthesized fields written
    by the typed-cache sync postprocess hook. Without explicit fallback
    logic the response would render with just a bare SKU and no
    "Part of: …" line. ``_dict_to_variant_details`` handles this via:

    - ``parent_name_value = _attr(v, 'parent_name') or _attr(parent, 'name')``
      — falls back to the enriched parent's ``name`` when the variant
      itself has no precomputed field
    - ``display_name_value = _attr(v, 'display_name') or
      build_variant_display_name(parent_name_value, configs, sku)`` —
      recomputes the canonical display name from parent + configs

    This test exercises the path with an actual ``Variant`` attrs
    model (no cache-only fields) plus a parent product in the enriched
    cache, and asserts both names land correctly on the response.
    Regression test for #564.
    """
    from katana_public_api_client.client_types import UNSET
    from katana_public_api_client.models.variant import Variant
    from katana_public_api_client.models.variant_config_attributes_type_0_item import (
        VariantConfigAttributesType0Item,
    )
    from katana_public_api_client.models.variant_custom_fields_type_0_item import (
        VariantCustomFieldsType0Item,
    )
    from katana_public_api_client.models.variant_type import VariantType

    context, lifespan_ctx = create_mock_context()
    # The variant lookup misses the cache and falls through to the API.
    # The API returns a generated attrs ``Variant`` — no ``display_name``
    # or ``parent_name`` keys, because those are cache-synthesized fields.
    # NB: the attrs model's discriminator is ``type_`` (trailing underscore
    # — Python keyword collision in the generator), NOT ``type``. Pin
    # that in the fixture so the read-side fallback (``_attr(v, "type")
    # or _attr(v, "type_")``) gets exercised end-to-end.
    #
    # ``custom_fields`` is also populated alongside ``config_attributes``
    # so both attrs-item shapes round-trip through ``_dump_list``. The
    # ``_dump_list`` ``to_dict`` branch handles both lists, but only
    # exercising one would leave the other path uncovered.
    api_variant = Variant(
        id=9001,
        sku="KNF-PRO-8PC-STL",
        product_id=101,
        material_id=None,
        sales_price=299.99,
        purchase_price=150.0,
        type_=VariantType.PRODUCT,
        config_attributes=[
            VariantConfigAttributesType0Item(
                config_name="Piece Count", config_value="8-piece"
            ),
            VariantConfigAttributesType0Item(
                config_name="Handle Material", config_value="Steel"
            ),
        ],
        custom_fields=[
            VariantCustomFieldsType0Item(
                field_name="Warranty Period", field_value="5 years"
            ),
        ],
    )
    # The fixture deliberately leaves ``lead_time`` unset on the attrs
    # model so the test verifies optional-field omission round-trips
    # cleanly (UNSET on the attrs side → ``None`` on the response).
    # Mirrors a real API response shape where the seller hasn't
    # populated lead_time.
    assert api_variant.lead_time is UNSET, (
        "Fixture must leave lead_time as UNSET to mimic an API response "
        "where the optional field wasn't populated. If this fails the "
        "fixture has drifted, not the prod code."
    )

    # Cache miss for the variant; parent product + supplier ARE in cache
    # (the @cache_read decorator synced them before the call).
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(return_value=None)
    parent_product = {
        "id": 101,
        "name": "Professional Kitchen Knife Set",
        "uom": "set",
        "default_supplier_id": 555,
        "batch_tracked": False,
    }
    supplier = {"id": 555, "name": "Acme Cutlery Co"}

    async def _get_many_by_ids(entity_type, ids, **_kw):
        from katana_public_api_client.models_pydantic._generated import (
            CachedProduct,
            CachedSupplier,
        )

        if entity_type == CachedProduct:
            return {101: parent_product} if 101 in set(ids) else {}
        if entity_type == CachedSupplier:
            return {555: supplier} if 555 in set(ids) else {}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        side_effect=_get_many_by_ids
    )

    with patch(
        "katana_mcp.tools.foundation.items._fetch_variant_by_id",
        new_callable=AsyncMock,
        return_value=api_variant,
    ):
        request = GetVariantDetailsRequest(variant_id=9001)
        [result] = (await _get_variant_details_impl(request, context)).found

    # parent_name lifted from the enriched parent product
    assert result.product_or_material_name == "Professional Kitchen Knife Set"
    # display_name recomputed from parent_name + configs (parent + Piece
    # Count + Handle Material). Confirms ``build_variant_display_name``
    # is called on the API-fallback path, not just the cache-hit path.
    assert result.display_name is not None
    assert "Professional Kitchen Knife Set" in result.display_name
    assert "8-piece" in result.display_name
    assert "Steel" in result.display_name
    # Lifted parent context — the bits that would silently null on a
    # broken fallback path.
    assert result.uom == "set"
    assert result.default_supplier_id == 555
    assert result.default_supplier_name == "Acme Cutlery Co"
    # Variant-level fields still surface from the attrs model.
    assert result.sku == "KNF-PRO-8PC-STL"
    assert result.sales_price == 299.99
    # Both attrs-item lists ``_dump_list`` handles — config_attributes
    # AND custom_fields — round-trip into plain dicts on the response.
    # Pre-fix this assertion would have failed with a pydantic
    # ValidationError when ``_dump_list`` left the attrs items
    # unconverted.
    assert result.config_attributes == [
        {"config_name": "Piece Count", "config_value": "8-piece"},
        {"config_name": "Handle Material", "config_value": "Steel"},
    ]
    assert result.custom_fields == [
        {"field_name": "Warranty Period", "field_value": "5 years"},
    ]
    # ``type`` comes through the ``type_`` → ``type`` rename — pinned
    # because attrs models name the discriminator ``type_`` to avoid the
    # Python keyword collision, and a naive ``_attr(v, "type")`` would
    # silently return None on this path.
    assert result.type == "product"


@pytest.mark.asyncio
async def test_get_variant_details_cache_hit_and_api_fallback_paths_match():
    """The same logical variant must produce structurally identical
    ``VariantDetailsResponse`` whether resolved via the cache-hit path
    (``CachedVariant`` shape) or the API-fallback path (attrs ``Variant``
    shape). Every field surfaced through ``_dict_to_variant_details``
    needs to read off both shapes consistently.

    This is the divergence-protection contract that #564 and the Copilot
    review on PR #717 exposed two facets of:

    - ``_dump_list`` only handled ``model_dump`` (pydantic), not
      ``to_dict`` (attrs) — API-fallback variants with non-empty
      ``config_attributes`` would fail pydantic validation
    - ``_attr(v, "type")`` returned None on attrs because the field is
      named ``type_`` (Python-keyword rename), dropping the type badge

    Both bugs share the same root: cache rows and attrs models have
    subtly divergent field shapes, and any helper that reads them with
    a single attribute name will silently lose data on one side. The
    only practical defense is exercising both paths with the same
    logical input and asserting the responses match — catching a
    broader class of latent divergence without enumerating every
    possible field-shape difference.

    Adding new fields to ``VariantDetailsResponse`` that read from the
    variant: if the field's source differs between cache and attrs
    shapes (different name, different type), this test will fail and
    point at the divergence.
    """
    from katana_public_api_client.models.variant import Variant
    from katana_public_api_client.models.variant_config_attributes_type_0_item import (
        VariantConfigAttributesType0Item,
    )
    from katana_public_api_client.models.variant_custom_fields_type_0_item import (
        VariantCustomFieldsType0Item,
    )
    from katana_public_api_client.models.variant_type import VariantType

    # Logical variant + parent — same data, used to build both shapes.
    # Pinned values rather than the existing ``_FULL_VARIANT_DICT`` so
    # the test stays self-contained and the assertions read top-to-bottom.
    parent_product = {
        "id": 101,
        "name": "Professional Kitchen Knife Set",
        "uom": "set",
        "default_supplier_id": 555,
        "batch_tracked": False,
        "purchase_uom": None,
        "purchase_uom_conversion_rate": None,
    }
    supplier = {"id": 555, "name": "Acme Cutlery Co"}

    # CachedVariant shape: dict with cache-only synthesized fields
    # (``display_name``, ``parent_name``) precomputed at sync time.
    cache_row = {
        "id": 9001,
        "sku": "KNF-PRO-8PC-STL",
        "product_id": 101,
        "material_id": None,
        "sales_price": 299.99,
        "purchase_price": 150.0,
        "type": "product",
        "internal_barcode": "INT-KNF-001",
        "registered_barcode": "789123456789",
        "supplier_item_codes": ["SUP-KNF-8PC-001"],
        "lead_time": 7,
        "minimum_order_quantity": 1,
        "config_attributes": [
            {"config_name": "Piece Count", "config_value": "8-piece"},
            {"config_name": "Handle Material", "config_value": "Steel"},
        ],
        "custom_fields": [
            {"field_name": "Warranty Period", "field_value": "5 years"},
        ],
        "display_name": ("Professional Kitchen Knife Set / 8-piece / Steel"),
        "parent_name": "Professional Kitchen Knife Set",
        "created_at": None,
        "updated_at": None,
        "deleted_at": None,
    }

    # attrs Variant shape: same logical data, no cache-only fields,
    # ``type_`` trailing-underscore rename, attrs items for configs /
    # custom fields. The fields ``Variant`` doesn't carry
    # (display_name, parent_name) get recomputed at read time by
    # ``_dict_to_variant_details`` from the enriched parent.
    api_variant = Variant(
        id=9001,
        sku="KNF-PRO-8PC-STL",
        product_id=101,
        material_id=None,
        sales_price=299.99,
        purchase_price=150.0,
        type_=VariantType.PRODUCT,
        internal_barcode="INT-KNF-001",
        registered_barcode="789123456789",
        supplier_item_codes=["SUP-KNF-8PC-001"],
        lead_time=7,
        minimum_order_quantity=1,
        config_attributes=[
            VariantConfigAttributesType0Item(
                config_name="Piece Count", config_value="8-piece"
            ),
            VariantConfigAttributesType0Item(
                config_name="Handle Material", config_value="Steel"
            ),
        ],
        custom_fields=[
            VariantCustomFieldsType0Item(
                field_name="Warranty Period", field_value="5 years"
            ),
        ],
    )
    # Sanity: the attrs shape genuinely lacks cache-only fields. If
    # this changes the test stops proving what it claims to prove.
    assert api_variant.lead_time == 7  # actually-set field surfaces
    assert not hasattr(api_variant, "display_name")
    assert not hasattr(api_variant, "parent_name")

    async def _get_many_by_ids(entity_type, ids, **_kw):
        from katana_public_api_client.models_pydantic._generated import (
            CachedProduct,
            CachedSupplier,
        )

        if entity_type == CachedProduct:
            return {101: parent_product} if 101 in set(ids) else {}
        if entity_type == CachedSupplier:
            return {555: supplier} if 555 in set(ids) else {}
        return {}

    async def _run_path(variant_lookup_returns: object) -> dict:
        """Drive the impl with a single mocked variant return value; return
        the response as a plain dict for cross-path comparison."""
        context, lifespan_ctx = create_mock_context()
        lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(
            return_value=variant_lookup_returns
        )
        lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
            side_effect=_get_many_by_ids
        )
        # API path: cache_by_id returns None, _fetch_variant_by_id falls
        # through to its API call. Patch the inner call to return the
        # attrs Variant directly without round-tripping through httpx.
        if variant_lookup_returns is None:
            with patch(
                "katana_mcp.tools.foundation.items._fetch_variant_by_id",
                new_callable=AsyncMock,
                return_value=api_variant,
            ):
                request = GetVariantDetailsRequest(variant_id=9001)
                response = (await _get_variant_details_impl(request, context)).found[0]
        else:
            request = GetVariantDetailsRequest(variant_id=9001)
            response = (await _get_variant_details_impl(request, context)).found[0]
        return response.model_dump()

    cache_response = await _run_path(cache_row)
    api_response = await _run_path(None)

    # Path equivalence — every user-facing field on
    # ``VariantDetailsResponse`` must produce the same value from either
    # path. A diff here is a divergence bug.
    assert cache_response == api_response, (
        "Cache-hit and API-fallback paths produced different responses. "
        "Diff (cache - api):\n"
        + "\n".join(
            f"  {k}: cache={cache_response.get(k)!r} api={api_response.get(k)!r}"
            for k in sorted(set(cache_response) | set(api_response))
            if cache_response.get(k) != api_response.get(k)
        )
    )


@pytest.mark.asyncio
async def test_get_variant_details_no_purchase_uom_when_parent_omits_it():
    """The common case (purchase_uom == stock uom) — parent omits the fields,
    response surfaces them as None so the Prefab UI card stays quiet."""
    context, lifespan_ctx = create_mock_context()
    variant = dict(_FULL_VARIANT_DICT)
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=variant)

    parent_product = {
        "id": 101,
        "uom": "pcs",
        "default_supplier_id": None,
        "batch_tracked": False,
    }

    async def _get_many_by_ids(entity_type, ids, **_kw):
        from katana_public_api_client.models_pydantic._generated import (
            CachedProduct,
        )

        if entity_type == CachedProduct:
            return {101: parent_product} if 101 in set(ids) else {}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        side_effect=_get_many_by_ids
    )

    request = GetVariantDetailsRequest(sku="KNF-PRO-8PC-STL")
    [result] = (await _get_variant_details_impl(request, context)).found

    assert result.purchase_uom is None
    assert result.purchase_uom_conversion_rate is None


# ============================================================================
# get_variant_details — partial-result batching (#617)
# ============================================================================
#
# Pre-#617 the impl raised on the first cache miss inside a batch, killing
# any other hits in the same call. The contract is now:
#
# - Singular convenience path (one ``sku=`` or ``variant_id=`` and no plural
#   list) — keep raising ``ValueError`` so the "that one variant doesn't
#   exist" UX stays clean.
# - Batch path (``skus=[...]`` / ``variant_ids=[...]`` or any mixed form) —
#   never short-circuit; return the hits in ``found`` and the misses in
#   ``not_found``.


@pytest.mark.asyncio
async def test_get_variant_details_batch_all_hits_returns_all_no_misses():
    """All-hits batch behaves identically to the pre-#617 path: every
    requested variant lands in ``found`` and ``not_found`` is empty."""
    context, lifespan_ctx = create_mock_context()
    by_sku = {
        "WIDGET-A": {"id": 1, "sku": "WIDGET-A", "display_name": "Widget A"},
        "WIDGET-B": {"id": 2, "sku": "WIDGET-B", "display_name": "Widget B"},
    }
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        side_effect=lambda sku, **_kw: by_sku.get(sku)
    )

    request = GetVariantDetailsRequest(skus=["WIDGET-A", "WIDGET-B"])
    result = await _get_variant_details_impl(request, context)

    assert [v.sku for v in result.found] == ["WIDGET-A", "WIDGET-B"]
    assert result.not_found == []


@pytest.mark.asyncio
async def test_get_variant_details_batch_partial_hits_returns_hits_and_misses():
    """A batch with one miss + one hit returns the hit in ``found`` and
    the missing identifier in ``not_found`` — no raise. This is the
    canonical receiving-flow case from #617."""
    context, lifespan_ctx = create_mock_context()
    by_sku = {
        "WIDGET-B": {"id": 2, "sku": "WIDGET-B", "display_name": "Widget B"},
    }
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        side_effect=lambda sku, **_kw: by_sku.get(sku)
    )

    request = GetVariantDetailsRequest(skus=["MISSING-A", "WIDGET-B"])
    result = await _get_variant_details_impl(request, context)

    assert [v.sku for v in result.found] == ["WIDGET-B"]
    assert len(result.not_found) == 1
    assert result.not_found[0].sku == "MISSING-A"
    assert result.not_found[0].variant_id is None


@pytest.mark.asyncio
async def test_get_variant_details_batch_all_misses_returns_empty_found():
    """An all-misses batch returns an empty ``found`` list and a
    populated ``not_found`` — no raise even though nothing resolved."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=None)

    request = GetVariantDetailsRequest(skus=["MISSING-A", "MISSING-B"])
    result = await _get_variant_details_impl(request, context)

    assert result.found == []
    assert [n.sku for n in result.not_found] == ["MISSING-A", "MISSING-B"]


@pytest.mark.asyncio
async def test_get_variant_details_singular_sku_miss_still_raises():
    """The singular convenience path (one ``sku=``) keeps raising
    ``ValueError`` on a miss — the partial-result contract only applies
    to the batch path."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=None)

    request = GetVariantDetailsRequest(sku="MISSING-SOLO")
    with pytest.raises(ValueError, match="Variant with SKU 'MISSING-SOLO' not found"):
        await _get_variant_details_impl(request, context)


@pytest.mark.asyncio
async def test_get_variant_details_singular_variant_id_miss_still_raises():
    """Singular ``variant_id=`` miss raises identically to singular
    ``sku=`` miss."""
    context, _lifespan_ctx = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.items._fetch_variant_by_id",
        new_callable=AsyncMock,
        return_value=None,
    ):
        request = GetVariantDetailsRequest(variant_id=99999)
        with pytest.raises(ValueError, match="Variant ID 99999 not found"):
            await _get_variant_details_impl(request, context)


@pytest.mark.asyncio
async def test_get_variant_details_mixed_skus_and_variant_ids_partial():
    """Mixed ``skus`` + ``variant_ids`` follows the batch contract — the
    caller is treating it as a batch, so misses on either side land in
    ``not_found`` rather than raising."""
    context, lifespan_ctx = create_mock_context()
    by_sku = {
        "WIDGET-OK": {"id": 1, "sku": "WIDGET-OK", "display_name": "Widget OK"},
    }
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        side_effect=lambda sku, **_kw: by_sku.get(sku)
    )

    by_id = {
        2: {"id": 2, "sku": "VAR-OK", "display_name": "Variant OK"},
    }

    async def _fetch(_services, vid):
        return by_id.get(vid)

    with patch(
        "katana_mcp.tools.foundation.items._fetch_variant_by_id",
        side_effect=_fetch,
    ):
        request = GetVariantDetailsRequest(
            skus=["WIDGET-OK", "MISSING-X"],
            variant_ids=[2, 99999],
        )
        result = await _get_variant_details_impl(request, context)

    assert sorted(v.sku for v in result.found) == ["VAR-OK", "WIDGET-OK"]
    assert {(n.sku, n.variant_id) for n in result.not_found} == {
        ("MISSING-X", None),
        (None, 99999),
    }


@pytest.mark.asyncio
async def test_get_variant_details_batch_content_surfaces_misses_in_json():
    """Batch JSON content carries a ``not_found`` array next to
    ``variants`` so callers see the gaps without a separate side-channel.
    Replaces the prior markdown-`Not found`-section test (#567 dropped
    the markdown layer)."""
    context, lifespan_ctx = create_mock_context()
    by_sku = {
        "WIDGET-B": {"id": 2, "sku": "WIDGET-B", "display_name": "Widget B"},
    }
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        side_effect=lambda sku, **_kw: by_sku.get(sku)
    )

    result = await get_variant_details(skus=["MISSING-A", "WIDGET-B"], context=context)

    data = json.loads(_content_text(result))
    assert {v["sku"] for v in data["variants"]} == {"WIDGET-B"}
    assert {n["sku"] for n in data["not_found"]} == {"MISSING-A"}


@pytest.mark.asyncio
async def test_get_variant_details_batch_json_includes_not_found():
    """Public tool's JSON rendering carries a ``not_found`` array next to
    ``variants`` so programmatic consumers can branch on it."""
    context, lifespan_ctx = create_mock_context()
    by_sku = {
        "WIDGET-B": {"id": 2, "sku": "WIDGET-B", "display_name": "Widget B"},
    }
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        side_effect=lambda sku, **_kw: by_sku.get(sku)
    )

    result = await get_variant_details(skus=["MISSING-A", "WIDGET-B"], context=context)

    payload = json.loads(_content_text(result))
    assert [v["sku"] for v in payload["variants"]] == ["WIDGET-B"]
    assert payload["not_found"] == [{"sku": "MISSING-A"}]


# ============================================================================
# VariantNotFound — XOR invariant on identifier shape
# ============================================================================


def test_variant_not_found_accepts_sku_only():
    """The canonical SKU-miss shape is valid."""
    miss = VariantNotFound(sku="MISSING-A")
    assert miss.sku == "MISSING-A"
    assert miss.variant_id is None


def test_variant_not_found_accepts_variant_id_only():
    """The canonical variant-id-miss shape is valid."""
    miss = VariantNotFound(variant_id=99999)
    assert miss.sku is None
    assert miss.variant_id == 99999


def test_variant_not_found_rejects_both_set():
    """Both identifiers set is invalid — would render an ambiguous miss
    line in markdown / leak both fields in JSON."""
    with pytest.raises(ValidationError, match="exactly one of 'sku' or 'variant_id'"):
        VariantNotFound(sku="MISSING-A", variant_id=99999)


def test_variant_not_found_rejects_both_none():
    """Both identifiers unset is invalid — markdown would render
    ``#None`` because the formatter falls back to ``variant_id`` when
    ``sku`` is None."""
    with pytest.raises(ValidationError, match="exactly one of 'sku' or 'variant_id'"):
        VariantNotFound()


# ============================================================================
# get_item — full field coverage across Product / Material / Service
# ============================================================================


_FETCH_ITEM_PATH = "katana_mcp.tools.foundation.items._fetch_item_attrs"


def _make_attrs(data: dict) -> MagicMock:
    """Wrap a dict as a MagicMock with to_dict() returning the dict.

    Mirrors the shape of a generated attrs model without pulling the real
    class — the tool only ever calls to_dict() on the result.
    """
    m = MagicMock()
    m.to_dict.return_value = data
    return m


_FULL_PRODUCT_DICT = {
    "id": 101,
    "name": "Professional Kitchen Knife Set",
    "type": "product",
    "uom": "set",
    "category_name": "Kitchenware",
    "is_sellable": True,
    "is_producible": True,
    "is_purchasable": False,
    "is_auto_assembly": True,
    "batch_tracked": True,
    "serial_tracked": False,
    "operations_in_sequence": False,
    "default_supplier_id": 1501,
    "additional_info": "Premium 8-piece set",
    "custom_field_collection_id": 201,
    "purchase_uom": "set",
    "purchase_uom_conversion_rate": 1.0,
    "lead_time": 5,
    "minimum_order_quantity": 2.0,
    "created_at": "2024-01-15T08:00:00+00:00",
    "updated_at": "2024-08-20T14:45:00+00:00",
    "archived_at": None,
    "deleted_at": None,
    "variants": [
        {
            "id": 3001,
            "sku": "KNF-PRO-8PC-STL",
            "type": "product",
            "sales_price": 299.99,
            "purchase_price": 150.0,
            "config_attributes": [
                {"config_name": "Piece Count", "config_value": "8-piece"},
                {"config_name": "Handle Material", "config_value": "Steel"},
            ],
        }
    ],
    "configs": [
        {
            "id": 501,
            "name": "Piece Count",
            "values": ["8-piece", "12-piece"],
            "product_id": 101,
            "material_id": None,
        }
    ],
    "supplier": {
        "id": 1501,
        "name": "Acme Cutlery Supply",
        "email": "sales@acme.example",
        "phone": "+1-555-0199",
        "currency": "USD",
        "comment": "Ships weekly",
        "default_address_id": 9001,
        "created_at": "2023-06-15T08:30:00+00:00",
        "updated_at": "2024-01-01T00:00:00+00:00",
    },
}


_FULL_MATERIAL_DICT = {
    "id": 3201,
    "name": "Stainless Steel Sheet 304",
    "type": "material",
    "uom": "m²",
    "category_name": "Raw Materials",
    "is_sellable": False,
    "batch_tracked": True,
    "serial_tracked": False,
    "operations_in_sequence": False,
    "default_supplier_id": 1502,
    "additional_info": "1.5mm thickness",
    "custom_field_collection_id": 202,
    "purchase_uom": "sheet",
    "purchase_uom_conversion_rate": 2.0,
    "created_at": "2024-01-10T10:00:00+00:00",
    "updated_at": "2024-01-15T14:30:00+00:00",
    "archived_at": None,
    "deleted_at": None,
    "variants": [
        {
            "id": 5001,
            "sku": "STEEL-304-1.5MM",
            "type": "material",
            "purchase_price": 45.0,
        }
    ],
    "configs": [
        {
            "id": 601,
            "name": "Grade",
            "values": ["304", "316"],
            "product_id": None,
            "material_id": 3201,
        }
    ],
    "supplier": None,
}


_FULL_SERVICE_DICT = {
    "id": 800,
    "name": "Laser Cutting Service",
    "type": "service",
    "uom": "hours",
    "category_name": "Outsourced Ops",
    "is_sellable": True,
    "additional_info": "Vendor-provided",
    "custom_field_collection_id": 77,
    "created_at": "2024-02-10T10:00:00+00:00",
    "updated_at": "2024-04-15T14:30:00+00:00",
    "archived_at": "2024-06-15T00:00:00+00:00",
    "deleted_at": None,
    "variants": [
        {
            "id": 9001,
            "sku": "SVC-LASER",
            "type": "service",
            "sales_price": 75.0,
            "default_cost": 40.0,
        }
    ],
}


@pytest.mark.asyncio
async def test_get_item_product_surfaces_every_field():
    """Every Product attrs field surfaces (plus nested variants/configs/supplier)."""
    context, _ = create_mock_context()
    attrs_product = _make_attrs(_FULL_PRODUCT_DICT)

    request = GetItemRequest(id=101, type=ItemType.PRODUCT)
    with patch(_FETCH_ITEM_PATH, AsyncMock(return_value=attrs_product)):
        result = await _get_item_impl(request, context)

    # Core
    assert result.id == 101
    assert result.name == "Professional Kitchen Knife Set"
    assert result.type == ItemType.PRODUCT
    assert result.uom == "set"
    assert result.category_name == "Kitchenware"
    assert result.is_sellable is True
    assert result.additional_info == "Premium 8-piece set"
    assert result.custom_field_collection_id == 201
    # Timestamps
    assert result.created_at == "2024-01-15T08:00:00+00:00"
    assert result.updated_at == "2024-08-20T14:45:00+00:00"
    assert result.archived_at is None
    assert result.deleted_at is None
    # Convenience boolean derived from archived_at
    assert result.is_archived is False
    # Tracking & purchase
    assert result.batch_tracked is True
    assert result.serial_tracked is False
    assert result.operations_in_sequence is False
    assert result.purchase_uom == "set"
    assert result.purchase_uom_conversion_rate == 1.0
    # Supplier & ordering
    assert result.default_supplier_id == 1501
    assert result.lead_time == 5
    assert result.minimum_order_quantity == 2.0
    # Product-only capability flags
    assert result.is_producible is True
    assert result.is_purchasable is False
    assert result.is_auto_assembly is True
    # Nested
    assert len(result.variants) == 1
    assert result.variants[0].sku == "KNF-PRO-8PC-STL"
    assert result.variants[0].sales_price == 299.99
    # display_name follows the Katana-UI canonical format
    # ``"{parent_name} / {config1} / {config2}"`` via
    # ``build_variant_display_name`` — same formula as the typed cache's
    # ``CachedVariant.display_name`` column and ``VariantDetailsResponse``.
    assert (
        result.variants[0].display_name
        == "Professional Kitchen Knife Set / 8-piece / Steel"
    )
    assert len(result.configs) == 1
    assert result.configs[0].name == "Piece Count"
    assert result.configs[0].values == ["8-piece", "12-piece"]
    assert result.supplier is not None
    assert result.supplier.id == 1501
    assert result.supplier.email == "sales@acme.example"


@pytest.mark.asyncio
async def test_get_item_material_surfaces_every_field():
    """Every Material attrs field surfaces; product-only flags stay None."""
    context, _ = create_mock_context()
    attrs_material = _make_attrs(_FULL_MATERIAL_DICT)

    request = GetItemRequest(id=3201, type=ItemType.MATERIAL)
    with patch(_FETCH_ITEM_PATH, AsyncMock(return_value=attrs_material)):
        result = await _get_item_impl(request, context)

    assert result.id == 3201
    assert result.name == "Stainless Steel Sheet 304"
    assert result.type == ItemType.MATERIAL
    assert result.uom == "m²"
    assert result.category_name == "Raw Materials"
    assert result.is_sellable is False
    assert result.batch_tracked is True
    assert result.default_supplier_id == 1502
    assert result.purchase_uom == "sheet"
    assert result.purchase_uom_conversion_rate == 2.0
    assert result.custom_field_collection_id == 202
    assert result.additional_info == "1.5mm thickness"
    assert result.created_at == "2024-01-10T10:00:00+00:00"
    # Product-only flags not on Material stay None
    assert result.is_producible is None
    assert result.is_purchasable is None
    assert result.is_auto_assembly is None
    assert result.lead_time is None
    assert result.minimum_order_quantity is None
    # Nested
    assert len(result.variants) == 1
    assert result.variants[0].sku == "STEEL-304-1.5MM"
    assert len(result.configs) == 1
    assert result.configs[0].name == "Grade"
    # No supplier record on this material (default_supplier_id set, supplier None)
    assert result.supplier is None


@pytest.mark.asyncio
async def test_get_item_service_surfaces_every_field():
    """Every Service attrs field surfaces; Product/Material-only fields stay None."""
    context, _ = create_mock_context()
    attrs_service = _make_attrs(_FULL_SERVICE_DICT)

    request = GetItemRequest(id=800, type=ItemType.SERVICE)
    with patch(_FETCH_ITEM_PATH, AsyncMock(return_value=attrs_service)):
        result = await _get_item_impl(request, context)

    assert result.id == 800
    assert result.name == "Laser Cutting Service"
    assert result.type == ItemType.SERVICE
    assert result.uom == "hours"
    assert result.category_name == "Outsourced Ops"
    assert result.is_sellable is True
    assert result.additional_info == "Vendor-provided"
    assert result.custom_field_collection_id == 77
    assert result.created_at == "2024-02-10T10:00:00+00:00"
    assert result.updated_at == "2024-04-15T14:30:00+00:00"
    assert result.archived_at == "2024-06-15T00:00:00+00:00"
    assert result.deleted_at is None
    # Convenience boolean — non-null archived_at means archived
    assert result.is_archived is True
    # Product/Material-only fields are None on Service
    assert result.batch_tracked is None
    assert result.default_supplier_id is None
    assert result.purchase_uom is None
    assert result.is_producible is None
    assert result.is_purchasable is None
    assert result.is_auto_assembly is None
    assert result.lead_time is None
    # ServiceVariant summary — default_cost aliased to purchase_price in summary
    assert len(result.variants) == 1
    assert result.variants[0].sku == "SVC-LASER"
    assert result.variants[0].sales_price == 75.0
    assert result.variants[0].purchase_price == 40.0
    # Service has no configs or supplier fields
    assert result.configs == []
    assert result.supplier is None


# ============================================================================
# get_item — markdown labels
# ============================================================================


@pytest.mark.asyncio
async def test_get_item_format_json_round_trips_nested():
    """format='json' emits the full response including nested variants/configs/supplier."""
    context, _ = create_mock_context()
    attrs_product = _make_attrs(_FULL_PRODUCT_DICT)

    with patch(_FETCH_ITEM_PATH, AsyncMock(return_value=attrs_product)):
        result = await get_item(id=101, type="product", context=context)

    data = json.loads(_content_text(result))
    assert data["id"] == 101
    assert data["batch_tracked"] is True
    assert data["is_auto_assembly"] is True
    assert data["variants"][0]["sku"] == "KNF-PRO-8PC-STL"
    assert data["configs"][0]["name"] == "Piece Count"
    assert data["supplier"]["email"] == "sales@acme.example"


# ============================================================================
# Post-review regression tests (/review-pr on #356)
# ============================================================================


def test_variant_to_summary_preserves_zero_purchase_price():
    """Regression: `or` treats 0.0 as falsy and used to shadow a legitimate
    zero-price variant with `default_cost`. Explicit None-check must keep
    the real 0.0 rather than falling through."""
    from katana_mcp.tools.foundation.items import _variant_to_summary

    summary = _variant_to_summary(
        {
            "id": 501,
            "sku": "FREE-SAMPLE",
            "sales_price": 0.0,
            "purchase_price": 0.0,
            "default_cost": 99.99,
            "type": "product",
        }
    )

    assert summary is not None
    assert summary.purchase_price == 0.0  # Real zero, not default_cost shadow


def test_variant_to_summary_falls_back_to_default_cost_when_purchase_price_absent():
    """When purchase_price is truly absent/None, default_cost is the fallback
    (matches ServiceVariant vs Variant shape divergence)."""
    from katana_mcp.tools.foundation.items import _variant_to_summary

    summary = _variant_to_summary(
        {
            "id": 502,
            "sku": "SRV-ITEM",
            "default_cost": 50.0,
            "type": "service",
        }
    )

    assert summary is not None
    assert summary.purchase_price == 50.0


def test_variant_to_summary_builds_canonical_display_name_with_parent_and_configs():
    """``_variant_to_summary`` populates ``display_name`` via the canonical
    helper (``parent / value1 / value2``) when a ``parent_name`` is supplied.
    Mirrors how every other variant-displaying surface formats the name —
    typed-cache ``CachedVariant.display_name``, ``VariantDetailsResponse.display_name``,
    and ``KatanaVariant.get_display_name`` all delegate to
    ``build_variant_display_name``, and the embedded variant summary must
    match.
    """
    from katana_mcp.tools.foundation.items import _variant_to_summary

    summary = _variant_to_summary(
        {
            "id": 7001,
            "sku": "KNF-PRO-8PC-STL",
            "sales_price": 299.99,
            "type": "product",
            "config_attributes": [
                {"config_name": "Piece Count", "config_value": "8-piece"},
                {"config_name": "Handle Material", "config_value": "Steel"},
            ],
        },
        parent_name="Professional Kitchen Knife Set",
    )

    assert summary is not None
    assert summary.display_name == "Professional Kitchen Knife Set / 8-piece / Steel"


def test_variant_to_summary_display_name_falls_back_to_sku_without_parent():
    """When no ``parent_name`` is supplied (helper called bare), the
    Katana-UI display falls back to the SKU — matches
    ``build_variant_display_name(None, [], sku)`` behaviour.
    """
    from katana_mcp.tools.foundation.items import _variant_to_summary

    summary = _variant_to_summary({"id": 7002, "sku": "ORPHAN-1"})

    assert summary is not None
    # Empty parent → falls back to the SKU (canonical helper contract).
    assert summary.display_name == "ORPHAN-1"


# ============================================================================
# katana_url deep-link wiring (#442)
# ============================================================================


@pytest.fixture
def _no_web_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin tests to the default `factory.katanamrp.com` base, regardless of
    whatever the developer/CI happened to export in ``KATANA_WEB_BASE_URL``.
    Without this, the URL-equality assertions below fail in environments that
    point at a non-default Katana domain.
    """
    monkeypatch.delenv("KATANA_WEB_BASE_URL", raising=False)


def test_dict_to_variant_details_uses_product_id_for_product_variants(
    _no_web_base_url: None,
):
    from katana_mcp.tools.foundation.items import _dict_to_variant_details

    response = _dict_to_variant_details(
        {"id": 1, "sku": "P-1", "product_id": 42, "material_id": None}
    )
    assert response.katana_url == "https://factory.katanamrp.com/product/42"


def test_dict_to_variant_details_falls_back_to_material_id_for_material_variants(
    _no_web_base_url: None,
):
    """Material-owned variants must link to the parent material via the
    distinct ``/material/{id}`` route (split from ``/product/{id}`` in #454
    once the live UI confirmed they're separate paths)."""
    from katana_mcp.tools.foundation.items import _dict_to_variant_details

    response = _dict_to_variant_details(
        {"id": 2, "sku": "M-1", "product_id": None, "material_id": 99}
    )
    assert response.katana_url == "https://factory.katanamrp.com/material/99"


def test_dict_to_variant_details_no_parent_returns_none_url():
    from katana_mcp.tools.foundation.items import _dict_to_variant_details

    response = _dict_to_variant_details(
        {"id": 3, "sku": "ORPHAN", "product_id": None, "material_id": None}
    )
    assert response.katana_url is None


def test_dict_to_variant_details_supplier_lifted_from_supplier_dict():
    """``default_supplier_name`` comes from the *supplier* dict, while
    ``default_supplier_id`` and ``uom`` come from the *parent* dict — pinning
    the source-of-truth contract so a future refactor can't quietly swap them.
    """
    from katana_mcp.tools.foundation.items import _dict_to_variant_details

    response = _dict_to_variant_details(
        {"id": 1, "sku": "P-1", "product_id": 42},
        parent={"uom": "ml", "default_supplier_id": 7, "batch_tracked": True},
        supplier={"name": "Acme Industrial"},
    )
    assert response.uom == "ml"
    assert response.default_supplier_id == 7
    assert response.default_supplier_name == "Acme Industrial"
    assert response.is_batch_tracked is True


@pytest.mark.asyncio
async def test_enrich_variants_keeps_product_and_material_maps_separate():
    """Product IDs and material IDs are NOT guaranteed disjoint (the cache
    keys rows by ``(entity_type, id)``). A previous version merged them into
    one ``parent_by_id`` keyed on numeric ID, which would mis-attach a
    material parent to a product variant when IDs collided. This test
    constructs a colliding-ID scenario and pins the per-type lookup so the
    bug can't regress (Copilot review on #542).
    """
    from katana_mcp.tools.foundation.items import _enrich_variants_with_parent

    from katana_public_api_client.models_pydantic._generated import (
        CachedMaterial,
        CachedProduct,
        CachedSupplier,
    )

    services = MagicMock()
    services.typed_cache.catalog = MagicMock()
    services.typed_cache.catalog.get_many_by_ids = AsyncMock(
        side_effect=lambda entity_type, _ids, **_kw: {
            CachedProduct: {42: {"id": 42, "uom": "pcs", "name": "Widget"}},
            CachedMaterial: {42: {"id": 42, "uom": "ml", "name": "Sealant"}},
            CachedSupplier: {},
        }[entity_type]
    )

    variants = [
        {"id": 1, "sku": "P-COL", "product_id": 42},
        {"id": 2, "sku": "M-COL", "material_id": 42},
    ]
    products, materials, _ = await _enrich_variants_with_parent(services, variants)

    assert products[42]["uom"] == "pcs"
    assert products[42]["name"] == "Widget"
    assert materials[42]["uom"] == "ml"
    assert materials[42]["name"] == "Sealant"


def test_item_katana_url_returns_none_for_service_type(_no_web_base_url: None):
    """Services have no per-item page in Katana's web app. Products and
    materials route to distinct singular paths (``/product/{id}`` and
    ``/material/{id}`` respectively)."""
    from katana_mcp.tools.foundation.items import _item_katana_url

    assert _item_katana_url(ItemType.SERVICE, 123) is None
    assert (
        _item_katana_url(ItemType.PRODUCT, 123)
        == "https://factory.katanamrp.com/product/123"
    )
    assert (
        _item_katana_url(ItemType.MATERIAL, 456)
        == "https://factory.katanamrp.com/material/456"
    )


# ============================================================================
# create_item — variant-field forwarding (Entity A — issue #627)
# ============================================================================


@pytest.mark.asyncio
async def test_create_item_product_forwards_variant_fields():
    """Variant-level fields supplied to create_item with type=product should
    land on the embedded CreateVariantRequest. Symmetric with create_product
    (#627)."""
    from katana_mcp.tools.foundation.items import (
        CreateItemRequest,
        VariantConfigAttributePatch,
        _create_item_impl,
    )

    from katana_public_api_client.models import (
        CreateVariantRequestConfigAttributesItem as ApiCreateVariantConfigItem,
    )

    context, lifespan_ctx = create_mock_context()
    mock_product = _mock_item(id=900, name="Variant Item")
    lifespan_ctx.client.products.create = AsyncMock(return_value=mock_product)

    request = CreateItemRequest(
        type=ItemType.PRODUCT,
        name="Variant Item",
        sku="VI-001",
        supplier_item_codes=["MPN-A", "MPN-B"],
        internal_barcode="INT-VI-001",
        registered_barcode="0000000000000",
        lead_time=10,
        minimum_order_quantity=2.5,
        config_attributes=[
            VariantConfigAttributePatch(config_name="Size", config_value="L"),
        ],
    )
    await _create_item_impl(request, context)

    variant = lifespan_ctx.client.products.create.call_args[0][0].variants[0]
    assert variant.supplier_item_codes == ["MPN-A", "MPN-B"]
    assert variant.internal_barcode == "INT-VI-001"
    assert variant.registered_barcode == "0000000000000"
    assert variant.lead_time == 10
    assert variant.minimum_order_quantity == 2.5
    assert len(variant.config_attributes) == 1
    assert isinstance(variant.config_attributes[0], ApiCreateVariantConfigItem)
    assert variant.config_attributes[0].config_name == "Size"
    assert variant.config_attributes[0].config_value == "L"


@pytest.mark.asyncio
async def test_create_item_material_forwards_variant_fields():
    """Mirror for type=material — same forwarding contract."""
    from katana_mcp.tools.foundation.items import (
        CreateItemRequest,
        _create_item_impl,
    )

    context, lifespan_ctx = create_mock_context()
    mock_material = _mock_item(id=901, name="Variant Material")
    lifespan_ctx.client.materials.create = AsyncMock(return_value=mock_material)

    request = CreateItemRequest(
        type=ItemType.MATERIAL,
        name="Variant Material",
        sku="VM-001",
        supplier_item_codes=["QBP-12345"],
        internal_barcode="INT-VM-001",
        lead_time=14,
    )
    await _create_item_impl(request, context)

    variant = lifespan_ctx.client.materials.create.call_args[0][0].variants[0]
    assert variant.supplier_item_codes == ["QBP-12345"]
    assert variant.internal_barcode == "INT-VM-001"
    assert variant.lead_time == 14


@pytest.mark.asyncio
async def test_create_item_omits_unset_variant_fields():
    """When variant fields aren't supplied to create_item, they must be UNSET
    on the API request (not None) — mirrors the create_product / create_material
    UNSET contract."""
    from katana_mcp.tools.foundation.items import (
        CreateItemRequest,
        _create_item_impl,
    )

    from katana_public_api_client.client_types import UNSET

    context, lifespan_ctx = create_mock_context()
    mock_product = _mock_item(id=902, name="Plain Item")
    lifespan_ctx.client.products.create = AsyncMock(return_value=mock_product)

    request = CreateItemRequest(type=ItemType.PRODUCT, name="Plain Item", sku="PI-001")
    await _create_item_impl(request, context)

    variant = lifespan_ctx.client.products.create.call_args[0][0].variants[0]
    assert variant.supplier_item_codes is UNSET
    assert variant.internal_barcode is UNSET
    assert variant.registered_barcode is UNSET
    assert variant.lead_time is UNSET
    assert variant.minimum_order_quantity is UNSET
    assert variant.config_attributes is UNSET


@pytest.mark.asyncio
async def test_create_item_forwards_purchase_uom_for_product():
    """purchase_uom + conversion_rate must land on the parent-level
    CreateProductRequest, and be mirrored back on CreateItemResponse so the
    mutation card can render the kit-size."""
    from katana_mcp.tools.foundation.items import (
        CreateItemRequest,
        _create_item_impl,
    )

    context, lifespan_ctx = create_mock_context()
    mock_product = _mock_item(id=910, name="Spoke (kit-purchased)")
    mock_product.uom = "pcs"
    mock_product.purchase_uom = "kit"
    mock_product.purchase_uom_conversion_rate = 4.0
    lifespan_ctx.client.products.create = AsyncMock(return_value=mock_product)

    request = CreateItemRequest(
        type=ItemType.PRODUCT,
        name="Spoke (kit-purchased)",
        sku="SP0502",
        uom="pcs",
        purchase_uom="kit",
        purchase_uom_conversion_rate=4.0,
    )
    response = await _create_item_impl(request, context)

    api_request = lifespan_ctx.client.products.create.call_args[0][0]
    assert api_request.purchase_uom == "kit"
    assert api_request.purchase_uom_conversion_rate == 4.0
    assert response.uom == "pcs"
    assert response.purchase_uom == "kit"
    assert response.purchase_uom_conversion_rate == 4.0


@pytest.mark.asyncio
async def test_create_item_forwards_purchase_uom_for_material():
    """Material flow — "box of 100" spoke nipples case."""
    from katana_mcp.tools.foundation.items import (
        CreateItemRequest,
        _create_item_impl,
    )

    context, lifespan_ctx = create_mock_context()
    mock_material = _mock_item(id=911, name="Spoke Nipples")
    mock_material.uom = "pcs"
    mock_material.purchase_uom = "box"
    mock_material.purchase_uom_conversion_rate = 100.0
    lifespan_ctx.client.materials.create = AsyncMock(return_value=mock_material)

    request = CreateItemRequest(
        type=ItemType.MATERIAL,
        name="Spoke Nipples",
        sku="SP7025",
        uom="pcs",
        purchase_uom="box",
        purchase_uom_conversion_rate=100.0,
    )
    response = await _create_item_impl(request, context)

    api_request = lifespan_ctx.client.materials.create.call_args[0][0]
    assert api_request.purchase_uom == "box"
    assert api_request.purchase_uom_conversion_rate == 100.0
    assert response.purchase_uom == "box"
    assert response.purchase_uom_conversion_rate == 100.0


@pytest.mark.asyncio
async def test_create_item_service_ignores_purchase_uom():
    """Services don't model purchase_uom — the field must be silently dropped,
    not crash, and not appear on the CreateServiceRequest. Response surfaces
    None so the mutation card stays quiet for services.
    """
    from katana_mcp.tools.foundation.items import (
        CreateItemRequest,
        _create_item_impl,
    )

    context, lifespan_ctx = create_mock_context()
    mock_service = MagicMock(spec=["id", "name"])
    mock_service.id = 912
    mock_service.name = "Consulting Service"
    lifespan_ctx.client.services.create = AsyncMock(return_value=mock_service)

    request = CreateItemRequest(
        type=ItemType.SERVICE,
        name="Consulting Service",
        sku="SVC-002",
        sales_price=150.0,
        purchase_uom="kit",
        purchase_uom_conversion_rate=4.0,
    )
    response = await _create_item_impl(request, context)

    api_request = lifespan_ctx.client.services.create.call_args[0][0]
    assert not hasattr(api_request, "purchase_uom")
    assert response.purchase_uom is None
    assert response.purchase_uom_conversion_rate is None


@pytest.mark.asyncio
async def test_create_item_service_ignores_variant_fields():
    """Services don't have variants in the same sense — pricing lives on the
    header. Variant-level fields supplied with type=service must not crash and
    must not appear on the service variant request."""
    from katana_mcp.tools.foundation.items import (
        CreateItemRequest,
        _create_item_impl,
    )

    context, lifespan_ctx = create_mock_context()
    # spec= constrains attrs so getattr(result, "uom", None) returns None
    # instead of auto-vivifying a MagicMock — services don't carry uom /
    # purchase_uom, so this mirrors real-API behavior.
    mock_service = MagicMock(spec=["id", "name"])
    mock_service.id = 903
    mock_service.name = "Consulting Service"
    lifespan_ctx.client.services.create = AsyncMock(return_value=mock_service)

    request = CreateItemRequest(
        type=ItemType.SERVICE,
        name="Consulting Service",
        sku="SVC-001",
        sales_price=150.0,
        # Supplied but should be ignored for service type
        supplier_item_codes=["IGNORED"],
        internal_barcode="ALSO-IGNORED",
    )
    await _create_item_impl(request, context)

    api_request = lifespan_ctx.client.services.create.call_args[0][0]
    service_variant = api_request.variants[0]
    # Service variant model has sku/sales_price/default_cost — no barcodes,
    # so the fields must not be passed through.
    assert (
        not hasattr(service_variant, "internal_barcode")
        or not getattr(service_variant, "internal_barcode", None)
        or service_variant.internal_barcode is None
    )


# ============================================================================
# CreateItemRequest — purchase_uom validator
# ============================================================================


def test_create_item_purchase_uom_requires_conversion_rate():
    """Setting purchase_uom without a conversion rate is ambiguous and must
    be caught at the MCP boundary, not silently forwarded to Katana."""
    from katana_mcp.tools.foundation.items import CreateItemRequest

    with pytest.raises(ValueError, match="purchase_uom_conversion_rate is required"):
        CreateItemRequest(
            type=ItemType.PRODUCT,
            name="Spoke",
            sku="SP-1",
            purchase_uom="kit",
        )


def test_create_item_conversion_rate_requires_purchase_uom():
    """Setting only the conversion rate is equally meaningless without a UoM."""
    from katana_mcp.tools.foundation.items import CreateItemRequest

    with pytest.raises(ValueError, match="purchase_uom is required"):
        CreateItemRequest(
            type=ItemType.PRODUCT,
            name="Spoke",
            sku="SP-1",
            purchase_uom_conversion_rate=4.0,
        )


def test_create_item_purchase_uom_rate_must_be_positive():
    """Zero or negative conversion rate has no meaningful interpretation."""
    from katana_mcp.tools.foundation.items import CreateItemRequest

    with pytest.raises(ValueError, match="must be greater than 0"):
        CreateItemRequest(
            type=ItemType.MATERIAL,
            name="Box",
            sku="BX-1",
            purchase_uom="box",
            purchase_uom_conversion_rate=0,
        )


# ============================================================================
# modify_item / delete_item — unified modification surface
# ============================================================================

_MODIFY_ITEM_UNWRAP_AS = "katana_mcp.tools._modification_dispatch.unwrap_as"
_MODIFY_ITEM_IS_SUCCESS = "katana_mcp.tools._modification_dispatch.is_success"


@pytest.mark.asyncio
async def test_modify_item_requires_at_least_one_subpayload():
    from katana_mcp.tools.foundation.items import (
        ModifyItemRequest,
        _modify_item_impl,
    )

    context, _ = create_mock_context()
    with pytest.raises(ValueError, match="At least one sub-payload"):
        await _modify_item_impl(
            ModifyItemRequest(id=42, type=ItemType.PRODUCT, preview=True), context
        )


@pytest.mark.asyncio
async def test_modify_item_rejects_misrouted_header_field():
    """Setting ``is_producible`` (PRODUCT-only) on a SERVICE raises before
    any API call."""
    from katana_mcp.tools.foundation.items import (
        ItemHeaderPatch,
        ModifyItemRequest,
        _modify_item_impl,
    )

    context, _ = create_mock_context()
    request = ModifyItemRequest(
        id=42,
        type=ItemType.SERVICE,
        update_header=ItemHeaderPatch(name="Renamed", is_producible=True),
        preview=True,
    )
    with pytest.raises(ValueError, match="not valid for type=service"):
        await _modify_item_impl(request, context)


@pytest.mark.asyncio
async def test_modify_item_rejects_variant_crud_for_services():
    from katana_mcp.tools.foundation.items import (
        ModifyItemRequest,
        VariantAdd,
        _modify_item_impl,
    )

    context, _ = create_mock_context()
    request = ModifyItemRequest(
        id=42,
        type=ItemType.SERVICE,
        add_variants=[VariantAdd(sku="V-1")],
        preview=True,
    )
    with pytest.raises(ValueError, match="not supported for SERVICE"):
        await _modify_item_impl(request, context)


@pytest.mark.asyncio
async def test_modify_item_product_header_dispatches_to_products_endpoint():
    """Confirms the type discriminator routes a PRODUCT header update to
    the API ``/products/{id}`` endpoint (and not ``/materials/{id}``).

    Note: this is the API path (still plural per Katana's REST conventions),
    not the web-app deep-link path (which is ``/product/{id}`` singular,
    see #454)."""
    from katana_mcp.tools.foundation.items import (
        ItemHeaderPatch,
        ModifyItemRequest,
        _modify_item_impl,
    )

    context, _ = create_mock_context()
    mock_product = MagicMock(name="UpdatedProduct")
    mock_product.id = 42
    mock_product.name = "Renamed Product"
    with (
        patch(
            "katana_public_api_client.api.product.update_product.asyncio_detailed",
            new_callable=AsyncMock,
        ) as mock_product_endpoint,
        patch(
            "katana_public_api_client.api.material.update_material.asyncio_detailed",
            new_callable=AsyncMock,
        ) as mock_material_endpoint,
        patch(
            "katana_public_api_client.api.product.get_product.asyncio_detailed",
            new_callable=AsyncMock,
        ),
        patch(_MODIFY_ITEM_UNWRAP_AS, return_value=mock_product),
    ):
        request = ModifyItemRequest(
            id=42,
            type=ItemType.PRODUCT,
            update_header=ItemHeaderPatch(name="Renamed Product", is_producible=True),
            preview=False,
        )
        response = await _modify_item_impl(request, context)

    assert response.is_preview is False
    assert response.entity_type == "product"
    assert response.actions[0].operation == "update_header"
    mock_product_endpoint.assert_awaited_once()
    mock_material_endpoint.assert_not_awaited()


@pytest.mark.asyncio
async def test_modify_item_material_header_dispatches_to_materials_endpoint():
    """Same shape as the PRODUCT test — pins the material-side routing."""
    from katana_mcp.tools.foundation.items import (
        ItemHeaderPatch,
        ModifyItemRequest,
        _modify_item_impl,
    )

    context, _ = create_mock_context()
    mock_material = _mock_item(id=99, name="Renamed Material")
    with (
        patch(
            "katana_public_api_client.api.material.update_material.asyncio_detailed",
            new_callable=AsyncMock,
        ) as mock_material_endpoint,
        patch(
            "katana_public_api_client.api.product.update_product.asyncio_detailed",
            new_callable=AsyncMock,
        ) as mock_product_endpoint,
        patch(
            "katana_public_api_client.api.material.get_material.asyncio_detailed",
            new_callable=AsyncMock,
        ),
        patch(_MODIFY_ITEM_UNWRAP_AS, return_value=mock_material),
    ):
        request = ModifyItemRequest(
            id=99,
            type=ItemType.MATERIAL,
            update_header=ItemHeaderPatch(name="Renamed Material"),
            preview=False,
        )
        response = await _modify_item_impl(request, context)

    assert response.entity_type == "material"
    mock_material_endpoint.assert_awaited_once()
    mock_product_endpoint.assert_not_awaited()


@pytest.mark.asyncio
async def test_modify_item_service_header_dispatches_to_services_endpoint():
    """SERVICE routing must hit ``/services/{id}``, not products or materials.
    Also pins ``katana_url=None`` for SERVICE (no Katana web page)."""
    from katana_mcp.tools.foundation.items import (
        ItemHeaderPatch,
        ModifyItemRequest,
        _modify_item_impl,
    )

    context, _ = create_mock_context()
    mock_service = MagicMock()
    mock_service.id = 7
    mock_service.name = "Renamed Service"
    with (
        patch(
            "katana_public_api_client.api.services.update_service.asyncio_detailed",
            new_callable=AsyncMock,
        ) as mock_service_endpoint,
        patch(
            "katana_public_api_client.api.product.update_product.asyncio_detailed",
            new_callable=AsyncMock,
        ) as mock_product_endpoint,
        patch(
            "katana_public_api_client.api.material.update_material.asyncio_detailed",
            new_callable=AsyncMock,
        ) as mock_material_endpoint,
        patch(
            "katana_public_api_client.api.services.get_service.asyncio_detailed",
            new_callable=AsyncMock,
        ),
        patch(_MODIFY_ITEM_UNWRAP_AS, return_value=mock_service),
    ):
        request = ModifyItemRequest(
            id=7,
            type=ItemType.SERVICE,
            update_header=ItemHeaderPatch(name="Renamed Service", sales_price=12.50),
            preview=False,
        )
        response = await _modify_item_impl(request, context)

    assert response.entity_type == "service"
    assert response.katana_url is None  # services have no Katana web page
    mock_service_endpoint.assert_awaited_once()
    mock_product_endpoint.assert_not_awaited()
    mock_material_endpoint.assert_not_awaited()


@pytest.mark.asyncio
async def test_modify_item_add_variant_injects_parent_id_for_product():
    from katana_mcp.tools.foundation.items import (
        ModifyItemRequest,
        VariantAdd,
        _modify_item_impl,
    )

    context, _ = create_mock_context()
    mock_variant = MagicMock(id=500)
    with (
        patch(
            "katana_public_api_client.api.variant.create_variant.asyncio_detailed",
            new_callable=AsyncMock,
        ) as mock_create,
        patch(
            "katana_public_api_client.api.product.get_product.asyncio_detailed",
            new_callable=AsyncMock,
        ),
        patch(_MODIFY_ITEM_UNWRAP_AS, return_value=mock_variant),
    ):
        request = ModifyItemRequest(
            id=42,
            type=ItemType.PRODUCT,
            add_variants=[VariantAdd(sku="NEW-SKU-1", sales_price=99.99)],
            preview=False,
        )
        response = await _modify_item_impl(request, context)

    assert response.actions[0].operation == "add_variant"
    mock_create.assert_awaited_once()
    assert mock_create.await_args is not None
    body = mock_create.await_args.kwargs["body"]
    assert body.product_id == 42
    # material_id should be UNSET, not 42 — it's a PRODUCT.
    from katana_public_api_client.client_types import UNSET

    assert body.material_id is UNSET


@pytest.mark.asyncio
async def test_delete_item_dispatches_to_typed_delete_endpoint():
    from katana_mcp.tools.foundation.items import (
        DeleteItemRequest,
        _delete_item_impl,
    )

    context, _ = create_mock_context()
    mock_response = MagicMock(status_code=204, parsed=None)
    with (
        patch(
            "katana_public_api_client.api.material.delete_material.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_delete,
        patch(
            "katana_public_api_client.api.product.delete_product.asyncio_detailed",
            new_callable=AsyncMock,
        ) as mock_product_delete,
        patch(
            "katana_public_api_client.api.material.get_material.asyncio_detailed",
            new_callable=AsyncMock,
        ),
        patch(_MODIFY_ITEM_IS_SUCCESS, return_value=True),
    ):
        request = DeleteItemRequest(id=99, type=ItemType.MATERIAL, preview=False)
        response = await _delete_item_impl(request, context)

    assert response.is_preview is False
    assert response.actions[0].succeeded is True
    mock_delete.assert_awaited_once()
    mock_product_delete.assert_not_awaited()


# ============================================================================
# #505 follow-on: PATCH-wipe `additional_info` workaround on items
# ============================================================================
#
# The Katana platform clears `additional_info` to `""` on PATCH whenever the
# field is omitted from the body — verified across PO/Material/Product/MO/
# StockAdjustment (see docs/KATANA_API_QUESTIONS.md §6.2). To work around it,
# `_build_update_header_request` echoes the existing value when the caller
# didn't change it.


def test_build_update_header_echoes_additional_info_when_unchanged():
    """Caller-supplied other field + populated existing notes → notes echoed
    in the PATCH body so Katana's wipe-on-omit doesn't fire."""
    from katana_mcp.tools.foundation.items import (
        ItemHeaderPatch,
        _build_update_header_request,
    )

    existing = MagicMock()
    existing.additional_info = "important supplier notes"

    req = _build_update_header_request(
        ItemHeaderPatch(name="RENAMED"), ItemType.MATERIAL, existing
    )

    assert req.to_dict() == {
        "name": "RENAMED",
        "additional_info": "important supplier notes",
    }


def test_build_update_header_does_not_echo_when_existing_is_empty():
    """No notes to preserve (empty string) → wire body stays minimal."""
    from katana_mcp.tools.foundation.items import (
        ItemHeaderPatch,
        _build_update_header_request,
    )

    existing = MagicMock()
    existing.additional_info = ""

    req = _build_update_header_request(
        ItemHeaderPatch(name="RENAMED"), ItemType.PRODUCT, existing
    )

    assert req.to_dict() == {"name": "RENAMED"}


def test_build_update_header_does_not_echo_when_existing_is_unset():
    """No notes to preserve (UNSET sentinel) → wire body stays minimal."""
    from katana_mcp.tools.foundation.items import (
        ItemHeaderPatch,
        _build_update_header_request,
    )

    from katana_public_api_client.client_types import UNSET

    existing = MagicMock()
    existing.additional_info = UNSET

    req = _build_update_header_request(
        ItemHeaderPatch(name="RENAMED"), ItemType.MATERIAL, existing
    )

    assert req.to_dict() == {"name": "RENAMED"}


def test_build_update_header_caller_explicit_additional_info_wins():
    """Caller-supplied additional_info beats the echo even if existing differs."""
    from katana_mcp.tools.foundation.items import (
        ItemHeaderPatch,
        _build_update_header_request,
    )

    existing = MagicMock()
    existing.additional_info = "old notes"

    req = _build_update_header_request(
        ItemHeaderPatch(name="RENAMED", additional_info="new notes"),
        ItemType.MATERIAL,
        existing,
    )

    assert req.to_dict() == {"name": "RENAMED", "additional_info": "new notes"}


def test_build_update_header_no_existing_skips_echo():
    """Without an existing-item snapshot, echo is skipped (best-effort)."""
    from katana_mcp.tools.foundation.items import (
        ItemHeaderPatch,
        _build_update_header_request,
    )

    req = _build_update_header_request(
        ItemHeaderPatch(name="RENAMED"), ItemType.MATERIAL, None
    )

    assert req.to_dict() == {"name": "RENAMED"}


# ============================================================================
# #503: configs / config_attributes propagate through modify_item
# ============================================================================


def test_build_update_header_product_configs_reaches_wire_body():
    """``configs`` on a PRODUCT update serializes to the API wire body — the
    bug in #503 was that the field was silently dropped before reaching the
    request DTO. With the fix, it appears in ``request.to_dict()`` as the
    Katana-shaped ``[{name, values}, ...]``."""
    from katana_mcp.tools.foundation.items import (
        ItemConfigPatch,
        ItemHeaderPatch,
        _build_update_header_request,
    )

    req = _build_update_header_request(
        ItemHeaderPatch(
            configs=[
                ItemConfigPatch(name="Teeth", values=["32", "34"]),
                ItemConfigPatch(name="Offset", values=["3mm"]),
            ]
        ),
        ItemType.PRODUCT,
        None,
    )

    body = req.to_dict()
    assert body["configs"] == [
        {"name": "Teeth", "values": ["32", "34"]},
        {"name": "Offset", "values": ["3mm"]},
    ]


def test_build_update_header_product_configs_drops_id():
    """The PRODUCT update DTO doesn't accept ``id`` on configs (only
    MATERIAL does). When a caller includes one, it must be stripped before
    reaching the wire — otherwise Katana 422s on ``additionalProperties``."""
    from katana_mcp.tools.foundation.items import (
        ItemConfigPatch,
        ItemHeaderPatch,
        _build_update_header_request,
    )

    req = _build_update_header_request(
        ItemHeaderPatch(configs=[ItemConfigPatch(id=999, name="Teeth", values=["32"])]),
        ItemType.PRODUCT,
        None,
    )

    body = req.to_dict()
    assert body["configs"] == [{"name": "Teeth", "values": ["32"]}]
    assert "id" not in body["configs"][0]


def test_build_update_header_material_configs_preserves_id_when_set():
    """MATERIAL update DTO accepts ``id`` to match existing configs by ID
    (vs. by ``name`` when omitted). Pin both branches."""
    from katana_mcp.tools.foundation.items import (
        ItemConfigPatch,
        ItemHeaderPatch,
        _build_update_header_request,
    )

    req = _build_update_header_request(
        ItemHeaderPatch(
            configs=[
                ItemConfigPatch(id=42, name="Grade", values=["A", "B"]),
                ItemConfigPatch(name="Finish", values=["Matte"]),
            ]
        ),
        ItemType.MATERIAL,
        None,
    )

    body = req.to_dict()
    assert body["configs"] == [
        {"id": 42, "name": "Grade", "values": ["A", "B"]},
        {"name": "Finish", "values": ["Matte"]},
    ]


@pytest.mark.asyncio
async def test_modify_item_rejects_configs_on_service():
    """SERVICE doesn't support ``configs`` — it's PRODUCT/MATERIAL only.
    ``_validate_header_for_type`` rejects before any API call, mirroring
    the existing rejection of other PRODUCT/MATERIAL-only fields."""
    from katana_mcp.tools.foundation.items import (
        ItemConfigPatch,
        ItemHeaderPatch,
        ModifyItemRequest,
        _modify_item_impl,
    )

    context, _ = create_mock_context()
    request = ModifyItemRequest(
        id=42,
        type=ItemType.SERVICE,
        update_header=ItemHeaderPatch(
            configs=[ItemConfigPatch(name="Tier", values=["Basic", "Pro"])]
        ),
        preview=True,
    )
    with pytest.raises(ValueError, match="not valid for type=service"):
        await _modify_item_impl(request, context)


def test_build_create_variant_request_passes_config_attributes():
    """``add_variants[].config_attributes`` reaches the variant POST body
    (regression for #503's third silent-drop case)."""
    from katana_mcp.tools.foundation.items import (
        VariantAdd,
        VariantConfigAttributePatch,
        _build_create_variant_request,
    )

    req = _build_create_variant_request(
        parent_id=42,
        item_type=ItemType.PRODUCT,
        variant=VariantAdd(
            sku="CK1459-TMP",
            config_attributes=[
                VariantConfigAttributePatch(config_name="Offset", config_value="3mm"),
                VariantConfigAttributePatch(config_name="Teeth", config_value="34"),
            ],
        ),
    )

    body = req.to_dict()
    assert body["product_id"] == 42
    assert body["config_attributes"] == [
        {"config_name": "Offset", "config_value": "3mm"},
        {"config_name": "Teeth", "config_value": "34"},
    ]


def test_build_update_variant_request_passes_config_attributes():
    """``update_variants[].config_attributes`` reaches the variant PATCH
    body. Pre-fix, this set was silently dropped from the wire body."""
    from katana_mcp.tools.foundation.items import (
        VariantConfigAttributePatch,
        VariantUpdate,
        _build_update_variant_request,
    )

    req = _build_update_variant_request(
        VariantUpdate(
            id=40312281,
            config_attributes=[
                VariantConfigAttributePatch(config_name="Teeth", config_value="34"),
            ],
        )
    )

    body = req.to_dict()
    assert body["config_attributes"] == [{"config_name": "Teeth", "config_value": "34"}]
    # ``id`` is the path parameter, not a body field — must not appear in body.
    assert "id" not in body
