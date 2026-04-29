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
