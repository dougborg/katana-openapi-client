"""Tests for the exhaustive get_variant_details / get_item path.

Scope: #346 items slice — pins the full-field-coverage contract and the
canonical-name markdown rendering so a future refactor can't silently drop
Variant / Product / Material / Service fields or revert to prettified
headers that LLM consumers misread (the SW7083 supplier_item_codes bug).
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.items import (
    GetItemRequest,
    GetVariantDetailsRequest,
    ItemType,
    _get_item_impl,
    _get_variant_details_impl,
    get_item,
    get_variant_details,
)

from tests.conftest import create_mock_context


def _content_text(result) -> str:
    """Extract the text of a ToolResult's first content block."""
    return result.content[0].text


# ============================================================================
# Shared patches — cache_sync decorator + API fetch helper
# ============================================================================


@pytest.fixture(autouse=True)
def _patch_cache_sync():
    """Patch variant sync for all unit tests.

    The @cache_read decorator caches sync functions in a module-level dict on
    first call, so patching the cache_sync module alone is not enough — we
    also need to clear and re-mock the cached mapping in the decorators module.
    """
    from katana_mcp.cache import EntityType
    from katana_mcp.tools import decorators

    mock_sync = AsyncMock()
    original = decorators._sync_fns
    decorators._sync_fns = {EntityType.VARIANT: mock_sync}
    try:
        with patch(
            "katana_mcp.cache_sync.ensure_variants_synced", new_callable=AsyncMock
        ):
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

    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=variant_dict)

    request = GetVariantDetailsRequest(sku="KNF-PRO-8PC-STL")
    results = await _get_variant_details_impl(request, context)
    result = results[0]

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
async def test_get_variant_details_format_json_includes_deleted_at():
    """format='json' round-trips deleted_at (the pre-#346 drop)."""
    context, lifespan_ctx = create_mock_context()
    variant = dict(_FULL_VARIANT_DICT)
    variant["deleted_at"] = "2024-09-01T12:00:00+00:00"
    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=variant)

    result = await get_variant_details(
        sku="KNF-PRO-8PC-STL", format="json", context=context
    )

    data = json.loads(_content_text(result))
    assert data["variants"][0]["deleted_at"] == "2024-09-01T12:00:00+00:00"


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
        result = await get_item(id=101, type="product", format="json", context=context)

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
    mock_material = MagicMock()
    mock_material.id = 99
    mock_material.name = "Renamed Material"
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
