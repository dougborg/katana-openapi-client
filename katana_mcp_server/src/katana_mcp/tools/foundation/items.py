"""Item management tools for Katana MCP Server.

Foundation tools for searching and managing items (variants, products, materials, services).
Items are things with SKUs - they appear in the "Items" tab of the Katana UI.
"""

from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field, model_validator

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools._modification import (
    ConfirmableRequest,
    ModificationResponse,
    compute_field_diff,
    make_response_verifier,
    patch_additional_info,
    to_tool_result,
)
from katana_mcp.tools._modification_dispatch import (
    ActionSpec,
    CacheMerge,
    EntityNaming,
    has_any_subpayload,
    make_delete_apply,
    make_patch_apply,
    make_post_apply,
    plan_creates,
    plan_deletes,
    plan_updates,
    run_delete_plan,
    run_modify_plan,
    safe_fetch_for_diff,
    unset_dict,
)
from katana_mcp.tools.decorators import cache_read
from katana_mcp.tools.list_coercion import CoercedIntListOpt, CoercedStrListOpt
from katana_mcp.tools.tool_result_utils import (
    UI_META,
    make_tool_result,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import EntityKind, katana_web_url
from katana_public_api_client.api.material import (
    delete_material as api_delete_material,
    get_material as api_get_material,
    update_material as api_update_material,
)
from katana_public_api_client.api.product import (
    delete_product as api_delete_product,
    get_product as api_get_product,
    update_product as api_update_product,
)
from katana_public_api_client.api.services import (
    delete_service as api_delete_service,
    get_service as api_get_service,
    update_service as api_update_service,
)
from katana_public_api_client.api.variant import (
    create_variant as api_create_variant,
    delete_variant as api_delete_variant,
    get_variant as api_get_variant,
    update_variant as api_update_variant,
)
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.domain.variant import build_variant_display_name
from katana_public_api_client.models import (
    CreateMaterialRequest,
    CreateProductRequest,
    CreateServiceRequest,
    CreateServiceVariantRequest,
    CreateVariantRequest as APICreateVariantRequest,
    CreateVariantRequestConfigAttributesItem as APICreateVariantConfigItem,
    Material,
    Product,
    Service,
    UpdateMaterialRequest as APIUpdateMaterialRequest,
    UpdateMaterialRequestConfigsItem as APIUpdateMaterialConfigsItem,
    UpdateProductRequest as APIUpdateProductRequest,
    UpdateProductRequestConfigsItem as APIUpdateProductConfigsItem,
    UpdateServiceRequest as APIUpdateServiceRequest,
    UpdateVariantRequest as APIUpdateVariantRequest,
    UpdateVariantRequestConfigAttributesItem as APIUpdateVariantConfigItem,
    Variant,
)
from katana_public_api_client.models_pydantic._generated import (
    CachedMaterial,
    CachedProduct,
    CachedSupplier,
    CachedVariant,
)

logger = get_logger(__name__)


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    """Read ``name`` from a cache row, attrs model, OR dict uniformly.

    Cached SQLModel rows expose plain attributes; attrs API models use
    the ``UNSET`` sentinel for missing optional fields; tests
    occasionally fixture in raw dicts (the legacy cache shape) — accept
    all three so call sites stay agnostic to which side filled the
    slot (cache hit vs. API-fallback vs. test fixture). Used by the
    variant-enrichment paths after the #472 Phase D migration.
    """
    if obj is None:
        return default
    if isinstance(obj, dict):
        val = obj.get(name, default)
    else:
        val = getattr(obj, name, default)
    return default if val is UNSET else val


# ============================================================================
# Shared Models
# ============================================================================


class ItemType(StrEnum):
    """Type of item - matches Katana API discriminator."""

    PRODUCT = "product"
    MATERIAL = "material"
    SERVICE = "service"


# ============================================================================
# Tool 1: search_items
# ============================================================================


class SearchItemsRequest(BaseModel):
    """Request model for searching items."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., description="Search query (name, SKU, etc.)")
    limit: int = Field(default=20, description="Maximum results to return")
    include_archived: bool = Field(
        default=False,
        description=(
            "Include archived items in results. Defaults to false so normal "
            "searches only see active items. Pass true to find an archived "
            "item — typically as a precursor to unarchiving it via modify_item "
            'with {"update_header": {"is_archived": false}}.'
        ),
    )


class ItemInfo(BaseModel):
    """Item information."""

    id: int
    sku: str
    name: str
    item_type: str = "unknown"
    is_sellable: bool
    stock_level: int | None = None
    is_archived: bool = False


class SearchItemsResponse(BaseModel):
    """Response containing search results."""

    items: list[ItemInfo]
    total_count: int


def _search_response_to_tool_result(
    response: SearchItemsResponse, query: str
) -> ToolResult:
    """Convert SearchItemsResponse to ToolResult with the Prefab UI.

    The Prefab DataTable row-click drill-down requires a SKU (the on-row
    binding is ``{{ $event.sku }}`` per #714), so SKU-less variants are
    filtered OUT of the rendered table — clicking them would otherwise
    invoke ``get_variant_details(sku=None)`` and fail. **But JSON content
    keeps every variant**, including SKU-less rows. Programmatic consumers
    deserve the full result set; only the interactive UI hides rows it
    can't make actionable. The two surfaces diverge intentionally here.
    """
    from katana_mcp.tools.prefab_ui import build_search_results_ui

    # UI: filter out SKU-less variants (row-click drill-down needs sku).
    ui_items = [item.model_dump() for item in response.items if item.sku]
    ui = build_search_results_ui(ui_items, query, len(ui_items))

    # ``content`` carries the full response (every variant, sku or no sku) so
    # JSON consumers don't silently lose data. ``structured_content`` carries
    # the Prefab UI envelope with the filtered row set for MCP-Apps hosts —
    # the two surfaces diverge intentionally per the docstring above.
    return ToolResult(
        content=response.model_dump_json(indent=2),
        structured_content=ui,
    )


@cache_read(CachedVariant)
async def _search_items_impl(
    request: SearchItemsRequest, context: Context
) -> SearchItemsResponse:
    """Search variants via cached FTS5 + fuzzy fallback."""
    if not request.query or not request.query.strip():
        raise ValueError("Search query cannot be empty")
    if request.limit <= 0:
        raise ValueError("Limit must be positive")

    services = get_services(context)
    variants = await services.typed_cache.catalog.smart_search(
        CachedVariant,
        request.query,
        limit=request.limit,
        include_archived=request.include_archived,
    )

    # Variants inherit archived state from their parent product/material;
    # ``parent_archived_at`` is denormalized at sync time on the
    # ``CachedVariant`` row (see ``_variant_postprocess`` in
    # ``typed_cache/sync.py``).
    def _item_type(v: Any) -> str:
        type_val = _attr(v, "type")
        if type_val is None:
            return "unknown"
        return type_val.value if hasattr(type_val, "value") else str(type_val)

    items_info = [
        ItemInfo(
            id=_attr(v, "id"),
            sku=_attr(v, "sku") or "",
            name=_attr(v, "display_name") or _attr(v, "sku") or "",
            item_type=_item_type(v),
            is_sellable=_item_type(v) == "product",
            stock_level=None,
            is_archived=_attr(v, "parent_archived_at") is not None,
        )
        for v in variants
    ]

    return SearchItemsResponse(items=items_info, total_count=len(items_info))


@observe_tool
@unpack_pydantic_params
async def search_items(
    request: Annotated[SearchItemsRequest, Unpack()], context: Context
) -> ToolResult:
    """Search for items (products, materials, services) by name or SKU — returns multiple matching items.

    Use this as the starting point when you need to find items. Returns item IDs
    and SKUs needed by other tools like create_purchase_order or check_inventory.
    For full details on a specific item, follow up with get_variant_details.

    By default, archived items are excluded. Pass ``include_archived=true`` to
    surface them (each row carries an ``is_archived`` flag). To unarchive an
    item once you've found it, call ``modify_item`` with the request body
    ``{"update_header": {"is_archived": false}}``.

    Query must not be empty. Default limit is 20 results.
    """
    response = await _search_items_impl(request, context)
    return _search_response_to_tool_result(response, request.query)


# ============================================================================
# Tool 2: create_item
# ============================================================================


def _validate_purchase_uom_pair(
    purchase_uom: str | None,
    purchase_uom_conversion_rate: float | None,
) -> None:
    """Enforce the purchase_uom / conversion-rate co-dependency.

    Both fields must be set together (or both omitted) and the rate must be
    positive. Raises ``ValueError`` so callers get a clear validation error
    at the MCP boundary instead of a 422 from Katana. Shared by
    ``CreateProductRequest`` / ``CreateMaterialRequest`` / ``CreateItemRequest``.
    """
    if purchase_uom is not None and purchase_uom_conversion_rate is None:
        raise ValueError(
            "purchase_uom_conversion_rate is required when purchase_uom is set"
        )
    if purchase_uom_conversion_rate is not None and purchase_uom is None:
        raise ValueError(
            "purchase_uom is required when purchase_uom_conversion_rate is set"
        )
    if purchase_uom_conversion_rate is not None and purchase_uom_conversion_rate <= 0:
        raise ValueError("purchase_uom_conversion_rate must be greater than 0")


class CreateItemRequest(BaseModel):
    """Create a new item (product, material, or service).

    This is a simplified interface for creating items with a single variant.
    For complex items with multiple variants and configurations, use the
    native API models directly.
    """

    model_config = ConfigDict(extra="forbid")

    type: ItemType = Field(..., description="Type of item to create")
    name: str = Field(..., description="Item name")
    sku: str = Field(..., description="SKU for the item variant")
    uom: str = Field(
        default="pcs", description="Unit of measure (e.g., pcs, kg, hours)"
    )
    category_name: str | None = Field(default=None, description="Category for grouping")
    is_sellable: bool = Field(default=True, description="Whether item can be sold")
    sales_price: float | None = Field(default=None, description="Sales price per unit")
    purchase_price: float | None = Field(
        default=None, description="Purchase cost per unit"
    )

    # Product-specific
    is_producible: bool = Field(
        default=False, description="Can be manufactured (products only)"
    )
    is_purchasable: bool = Field(
        default=True, description="Can be purchased (products/materials)"
    )

    # Optional common fields
    default_supplier_id: int | None = Field(
        default=None,
        description=("Default supplier ID. Look up via `list_suppliers`."),
    )
    purchase_uom: str | None = Field(
        default=None,
        description=(
            "Purchase unit of measure when buying in a different unit than the "
            "stock ``uom`` (e.g. ``kit`` / ``box`` / ``case``). Pair with "
            "``purchase_uom_conversion_rate`` to set the kit-size. Leave None "
            "when purchased and stocked in the same unit. Ignored for "
            "type=service."
        ),
    )
    purchase_uom_conversion_rate: float | None = Field(
        default=None,
        description=(
            "How many stock-``uom`` units are received per one ``purchase_uom`` "
            "unit (e.g. 4 for a 4-pcs kit, 100 for a box of 100). Required "
            "when ``purchase_uom`` is set. Ignored for type=service."
        ),
    )
    additional_info: str | None = Field(default=None, description="Additional notes")

    # Variant-level fields — apply only when type is product or material.
    # Services carry pricing on the header; these fields are ignored for type=service.
    supplier_item_codes: list[str] | None = Field(
        default=None,
        description=(
            "Supplier item codes (e.g. supplier MPNs). Use a list — Katana "
            "stores multiple codes per variant. Ignored for type=service."
        ),
    )
    internal_barcode: str | None = Field(
        default=None,
        description="Internal barcode for the variant. Ignored for type=service.",
    )
    registered_barcode: str | None = Field(
        default=None,
        description=(
            "Registered (e.g. UPC/EAN) barcode for the variant. "
            "Ignored for type=service."
        ),
    )
    lead_time: int | None = Field(
        default=None,
        description="Variant lead time in days. Ignored for type=service.",
    )
    minimum_order_quantity: float | None = Field(
        default=None,
        description=(
            "Minimum order quantity for the variant. Ignored for type=service."
        ),
    )
    config_attributes: list[VariantConfigAttributePatch] | None = Field(
        default=None,
        description=(
            "Pin one value per parent config to define this variant. Each "
            "``config_name`` must match a config on the parent and "
            "``config_value`` must be one of that config's allowed values. "
            "Only meaningful for multi-variant product/material — leave None "
            "for single-variant items and for type=service."
        ),
    )

    @model_validator(mode="after")
    def _check_purchase_uom_pair(self) -> CreateItemRequest:
        _validate_purchase_uom_pair(
            self.purchase_uom, self.purchase_uom_conversion_rate
        )
        return self


def _item_katana_url(item_type: ItemType, id: int | None) -> str | None:
    """Web URL for a product or material. Services have no URL pattern."""
    if id is None or item_type == ItemType.SERVICE:
        return None
    kind: EntityKind = "product" if item_type == ItemType.PRODUCT else "material"
    return katana_web_url(kind, id)


class CreateItemResponse(BaseModel):
    """Response from creating an item."""

    id: int
    name: str
    type: ItemType
    variant_id: int | None = None
    sku: str | None = None
    uom: str | None = None
    purchase_uom: str | None = None
    purchase_uom_conversion_rate: float | None = None
    success: bool = True
    message: str = "Item created successfully"
    katana_url: str | None = None


async def _create_item_impl(
    request: CreateItemRequest, context: Context
) -> CreateItemResponse:
    """Create a product, material, or service with a variant."""
    services = get_services(context)

    # Build variant (services use a different variant model)
    if request.type == ItemType.SERVICE:
        service_variant = CreateServiceVariantRequest(
            sku=request.sku,
            sales_price=to_unset(request.sales_price),
            default_cost=to_unset(request.purchase_price),
        )
        api_request = CreateServiceRequest(
            name=request.name,
            uom=request.uom,
            category_name=to_unset(request.category_name),
            is_sellable=request.is_sellable,
            variants=[service_variant],
        )
        result = await services.client.services.create(api_request)
    else:
        config_attrs = (
            coerce_variant_config_attributes(
                [c.model_dump() for c in request.config_attributes],
                APICreateVariantConfigItem,
            )
            if request.config_attributes is not None
            else None
        )
        variant = APICreateVariantRequest(
            sku=request.sku,
            sales_price=to_unset(request.sales_price),
            purchase_price=to_unset(request.purchase_price),
            supplier_item_codes=to_unset(request.supplier_item_codes),
            internal_barcode=to_unset(request.internal_barcode),
            registered_barcode=to_unset(request.registered_barcode),
            lead_time=to_unset(request.lead_time),
            minimum_order_quantity=to_unset(request.minimum_order_quantity),
            config_attributes=to_unset(config_attrs),
        )
        if request.type == ItemType.PRODUCT:
            api_request = CreateProductRequest(
                name=request.name,
                uom=request.uom,
                category_name=to_unset(request.category_name),
                is_sellable=request.is_sellable,
                is_producible=request.is_producible,
                is_purchasable=request.is_purchasable,
                default_supplier_id=to_unset(request.default_supplier_id),
                purchase_uom=to_unset(request.purchase_uom),
                purchase_uom_conversion_rate=to_unset(
                    request.purchase_uom_conversion_rate
                ),
                additional_info=to_unset(request.additional_info),
                variants=[variant],
            )
            result = await services.client.products.create(api_request)
        elif request.type == ItemType.MATERIAL:
            api_request = CreateMaterialRequest(
                name=request.name,
                uom=request.uom,
                category_name=to_unset(request.category_name),
                is_sellable=request.is_sellable,
                default_supplier_id=to_unset(request.default_supplier_id),
                purchase_uom=to_unset(request.purchase_uom),
                purchase_uom_conversion_rate=to_unset(
                    request.purchase_uom_conversion_rate
                ),
                additional_info=to_unset(request.additional_info),
                variants=[variant],
            )
            result = await services.client.materials.create(api_request)
        else:
            raise ValueError(f"Invalid item type: {request.type}")

    # No explicit invalidation needed: the typed cache pulls incremental
    # deltas via ``updated_at_min`` on every ``@cache_read``-decorated
    # call, so the next ``search_items`` / ``get_variant_details`` sees
    # the new row without a manual dirty bit.

    # Service items don't carry purchase_uom — Product/Material do.
    result_uom = unwrap_unset(getattr(result, "uom", None))
    result_purchase_uom = unwrap_unset(getattr(result, "purchase_uom", None))
    result_conversion_rate = unwrap_unset(
        getattr(result, "purchase_uom_conversion_rate", None)
    )

    result_name = result.name or request.name
    return CreateItemResponse(
        id=result.id,
        name=result_name,
        type=request.type,
        sku=request.sku,
        uom=result_uom,
        purchase_uom=result_purchase_uom,
        purchase_uom_conversion_rate=result_conversion_rate,
        message=f"{request.type.value.title()} '{result_name}' created successfully with SKU {request.sku}",
        katana_url=_item_katana_url(request.type, result.id),
    )


@observe_tool
@unpack_pydantic_params
async def create_item(
    request: Annotated[CreateItemRequest, Unpack()], context: Context
) -> ToolResult:
    """Create any item type (product, material, or service) in the Katana catalog.

    General-purpose item creation. PREFER create_product for finished goods or
    create_material for raw materials — those tools have simpler, dedicated parameters.
    Use this tool only for services or when the item type is determined dynamically.

    Creates the item with a single variant. Returns the new item ID.
    """
    from katana_mcp.tools.prefab_ui import build_item_mutation_ui

    response = await _create_item_impl(request, context)
    ui = build_item_mutation_ui(response.model_dump(), "Created")

    return make_tool_result(response, ui=ui)


# ============================================================================
# Tool 3: get_item
# ============================================================================


class GetItemRequest(BaseModel):
    """Request to get an item by ID."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Item ID")
    type: ItemType = Field(..., description="Type of item (product, material, service)")


class ItemSupplierInfo(BaseModel):
    """Supplier record embedded on a product or material."""

    id: int
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    currency: str | None = None
    comment: str | None = None
    default_address_id: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ItemConfigInfo(BaseModel):
    """Configuration attribute definition (e.g. Size / Color)."""

    id: int
    name: str
    values: list[str] = Field(default_factory=list)
    product_id: int | None = None
    material_id: int | None = None


class ItemVariantSummary(BaseModel):
    """Brief variant summary embedded in the product/material/service detail."""

    id: int
    sku: str | None = None
    """Variant SKU. ``None``-able to match Katana's wire contract —
    the platform has no DB-level constraint forcing SKU non-null, so
    consumers must tolerate ``None``. Display-side consumers should
    coalesce to ``""`` when rendering; ``display_name`` below already
    provides a non-empty title in the rare SKU-less case.
    """
    sales_price: float | None = None
    purchase_price: float | None = None
    type: str | None = None
    display_name: str = ""
    """Katana-UI-format human-readable name: ``"{parent_name} / {config1} / {config2}"``.

    Built via :func:`katana_public_api_client.domain.variant.build_variant_display_name`
    so it stays consistent with every other variant-displaying surface
    (typed-cache ``CachedVariant.display_name``, ``KatanaVariant.get_display_name``,
    ``VariantDetailsResponse.display_name``). The summary is embedded in the parent
    ``ItemDetailsResponse`` so the parent name is known at build time — that means
    ``display_name`` is always populated when the parent has variants.
    """


class ItemDetailsResponse(BaseModel):
    """Full item details. Exhaustive — every field Katana exposes on
    ``Product`` / ``Material`` / ``Service`` is surfaced per-type (the API is
    polymorphic, so not every field applies to every type; product-only and
    service-only fields stay ``None`` for the other types).

    Nested ``variants``, ``configs``, and ``supplier`` are surfaced in summary
    form so a single call can answer most catalog questions without
    drill-downs. For full per-variant detail (barcodes, supplier codes,
    custom fields), follow up with ``get_variant_details``.
    """

    # Core — present on all three types
    id: int
    name: str
    type: ItemType
    katana_url: str | None = None
    uom: str | None = None
    category_name: str | None = None
    is_sellable: bool | None = None
    additional_info: str | None = None
    custom_field_collection_id: int | None = None

    # Timestamps — present on all three
    created_at: str | None = None
    updated_at: str | None = None
    archived_at: str | None = None
    deleted_at: str | None = None

    # Convenience boolean derived from ``archived_at`` — saves callers from
    # having to know the timestamp/null convention. Pair with
    # ``modify_item`` and ``{"update_header": {"is_archived": ...}}`` to
    # toggle the state.
    is_archived: bool = False

    # Product / Material only
    default_supplier_id: int | None = None
    batch_tracked: bool | None = None
    purchase_uom: str | None = None
    purchase_uom_conversion_rate: float | None = None
    serial_tracked: bool | None = None
    operations_in_sequence: bool | None = None

    # Product only
    is_producible: bool | None = None
    is_purchasable: bool | None = None
    is_auto_assembly: bool | None = None
    lead_time: int | None = None
    minimum_order_quantity: float | None = None

    # Nested collections (Product/Material carry configs + supplier;
    # all three carry variants)
    variants: list[ItemVariantSummary] = Field(default_factory=list)
    configs: list[ItemConfigInfo] = Field(default_factory=list)
    supplier: ItemSupplierInfo | None = None


def _supplier_to_info(raw: Any) -> ItemSupplierInfo | None:
    """Convert an attrs Supplier (or dict) to ItemSupplierInfo."""
    if raw is None:
        return None
    d = raw.to_dict() if hasattr(raw, "to_dict") else raw
    if not isinstance(d, dict) or "id" not in d:
        return None
    return ItemSupplierInfo(
        id=d["id"],
        name=d.get("name"),
        email=d.get("email"),
        phone=d.get("phone"),
        currency=d.get("currency"),
        comment=d.get("comment"),
        default_address_id=d.get("default_address_id"),
        created_at=_iso_or_none(d.get("created_at")),
        updated_at=_iso_or_none(d.get("updated_at")),
    )


def _config_to_info(raw: Any) -> ItemConfigInfo | None:
    """Convert an attrs ItemConfig (or dict) to ItemConfigInfo."""
    d = raw.to_dict() if hasattr(raw, "to_dict") else raw
    if not isinstance(d, dict) or "id" not in d:
        return None
    return ItemConfigInfo(
        id=d["id"],
        name=d.get("name") or "",
        values=list(d.get("values") or []),
        product_id=d.get("product_id"),
        material_id=d.get("material_id"),
    )


def _variant_to_summary(
    raw: Any, *, parent_name: str | None = None
) -> ItemVariantSummary | None:
    """Convert a nested Variant/ServiceVariant attrs (or dict) to summary.

    When ``parent_name`` is supplied, the helper computes the canonical
    ``display_name`` (Katana-UI format ``"{parent_name} / {config1} / ..."``)
    via :func:`build_variant_display_name` so the embedded summary is
    consistent with every other variant-displaying surface. The summary
    is built inside :func:`_get_item_impl`, where the parent's ``name``
    is always available; callers in that path always pass it.
    """
    d = raw.to_dict() if hasattr(raw, "to_dict") else raw
    if not isinstance(d, dict) or "id" not in d or "sku" not in d:
        return None
    # ``sku`` may legitimately be ``None`` on the wire; coalesce only
    # for the display-name fallback. The model field accepts ``None``.
    raw_sku = d["sku"]
    display_name = build_variant_display_name(
        parent_name,
        d.get("config_attributes") or [],
        raw_sku or "",
    )
    return ItemVariantSummary(
        id=d["id"],
        sku=raw_sku,
        sales_price=d.get("sales_price"),
        # ServiceVariant uses default_cost; Variant uses purchase_price.
        # Explicit None-check — `or` would shadow a legitimate 0.0 price
        # (free samples, gift items) with default_cost.
        purchase_price=(
            d["purchase_price"]
            if d.get("purchase_price") is not None
            else d.get("default_cost")
        ),
        type=d.get("type") or d.get("type_"),
        display_name=display_name,
    )


def _item_attrs_to_dict(item: Any) -> dict[str, Any]:
    """Call ``to_dict()`` on a Product/Material/Service attrs model.

    Wraps the call so callers can rely on a plain-dict view across all three
    types without branching on instance type.
    """
    if hasattr(item, "to_dict"):
        return item.to_dict()
    return dict(item) if isinstance(item, dict) else {}


async def _fetch_item_attrs(services: Any, item_id: int, item_type: ItemType) -> Any:
    """Fetch a Product/Material/Service attrs model with supplier extension.

    Uses the raw API directly so every field on the generated model is
    surfaced. The domain helpers (``client.products.get``, etc.) return
    ``KatanaProduct`` / ``KatanaMaterial`` — curated Pydantic models that
    drop nested ``variants``, ``configs``, ``supplier``. For the exhaustive
    detail tool we need the full attrs shape.
    """
    from katana_public_api_client.api.material import get_material
    from katana_public_api_client.api.product import get_product
    from katana_public_api_client.api.services import get_service
    from katana_public_api_client.models.get_material_extend_item import (
        GetMaterialExtendItem,
    )
    from katana_public_api_client.models.get_product_extend_item import (
        GetProductExtendItem,
    )
    from katana_public_api_client.utils import unwrap

    # Each branch unwraps separately so each `unwrap` call sees a single
    # `Response[T]` rather than a union of three — `Response[T]` is
    # invariant, so `Response[A] | Response[B] | Response[C]` doesn't
    # unify under one `T` and pyright rejects the union form.
    if item_type == ItemType.PRODUCT:
        return unwrap(
            await get_product.asyncio_detailed(
                client=services.client,
                id=item_id,
                extend=[GetProductExtendItem.SUPPLIER],
            )
        )
    if item_type == ItemType.MATERIAL:
        return unwrap(
            await get_material.asyncio_detailed(
                client=services.client,
                id=item_id,
                extend=[GetMaterialExtendItem.SUPPLIER],
            )
        )
    return unwrap(
        await get_service.asyncio_detailed(client=services.client, id=item_id)
    )


async def _safe_fetch_item_attrs(
    services: Any, item_id: int, item_type: ItemType
) -> Any | None:
    """Best-effort variant of ``_fetch_item_attrs``: returns None on any error.

    Used as ``CacheMerge.refetch_for_merge`` so the dispatcher's
    ``_post_apply_cache_merge`` can short-circuit on fetch failure via
    its ``if parent is None: return`` guard — instead of unwinding
    through the outer best-effort handler with a misleading
    ``AuthenticationError`` / ``APIError`` traceback. Mirrors how
    ``safe_fetch_for_diff`` shields the existing diff-context path.
    """
    try:
        return await _fetch_item_attrs(services, item_id, item_type)
    except asyncio.CancelledError:
        # Cooperative cancellation must propagate, not get swallowed by
        # the best-effort handler — see the dispatcher's outer handler
        # for the same convention.
        raise
    except Exception as exc:
        logger.info(
            f"Post-apply refetch of {item_type.value} {item_id} for cache "
            f"merge failed: {type(exc).__name__}: {exc} — cache row may be "
            f"stale until next sync. Does not affect the API write."
        )
        return None


async def _get_item_impl(
    request: GetItemRequest, context: Context
) -> ItemDetailsResponse:
    """Get exhaustive item details by ID and type."""
    services = get_services(context)
    item = await _fetch_item_attrs(services, request.id, request.type)
    d = _item_attrs_to_dict(item)

    # Lift the parent's name into the variant summary builder so each
    # variant's ``display_name`` follows the canonical Katana-UI format
    # (parent / value1 / value2). Without this every nested variant
    # would fall back to its SKU (the empty-parent branch in
    # ``build_variant_display_name``).
    parent_name = d.get("name") or ""
    variants = [
        v
        for v in (
            _variant_to_summary(raw, parent_name=parent_name)
            for raw in d.get("variants") or []
        )
        if v
    ]
    configs = [c for c in (_config_to_info(raw) for raw in d.get("configs") or []) if c]
    supplier = _supplier_to_info(d.get("supplier"))

    item_id = d.get("id", request.id)
    # Katana represents archive state as ``archived_at: timestamp | null`` on
    # read; non-null = archived. The boolean ``is_archived`` is a convenience
    # field that mirrors Katana's own update-request convention so callers
    # can pair it with ``modify_item`` and
    # ``{"update_header": {"is_archived": ...}}``.
    return ItemDetailsResponse(
        id=item_id,
        name=d.get("name") or "",
        type=request.type,
        katana_url=_item_katana_url(request.type, item_id),
        uom=d.get("uom"),
        category_name=d.get("category_name"),
        is_sellable=d.get("is_sellable"),
        additional_info=d.get("additional_info"),
        custom_field_collection_id=d.get("custom_field_collection_id"),
        created_at=_iso_or_none(d.get("created_at")),
        updated_at=_iso_or_none(d.get("updated_at")),
        archived_at=_iso_or_none(d.get("archived_at")),
        deleted_at=_iso_or_none(d.get("deleted_at")),
        is_archived=d.get("archived_at") is not None,
        # Product / Material only (remain None on Service)
        default_supplier_id=d.get("default_supplier_id"),
        batch_tracked=d.get("batch_tracked"),
        purchase_uom=d.get("purchase_uom"),
        purchase_uom_conversion_rate=d.get("purchase_uom_conversion_rate"),
        serial_tracked=d.get("serial_tracked"),
        operations_in_sequence=d.get("operations_in_sequence"),
        # Product only
        is_producible=d.get("is_producible"),
        is_purchasable=d.get("is_purchasable"),
        is_auto_assembly=d.get("is_auto_assembly"),
        lead_time=d.get("lead_time"),
        minimum_order_quantity=d.get("minimum_order_quantity"),
        # Nested collections
        variants=variants,
        configs=configs,
        supplier=supplier,
    )


def _item_details_to_tool_result(response: ItemDetailsResponse) -> ToolResult:
    """Convert ItemDetailsResponse to ToolResult.

    content carries the raw response as JSON for the LLM (no UI tree noise);
    structured_content carries the Prefab envelope rendered in the iframe on
    UI-capable hosts (per MCP Apps spec, #422).
    """
    from katana_mcp.tools.prefab_ui import build_item_detail_ui

    ui = build_item_detail_ui(response.model_dump())
    return ToolResult(
        content=response.model_dump_json(),
        structured_content=ui,
    )


@observe_tool
@unpack_pydantic_params
async def get_item(
    request: Annotated[GetItemRequest, Unpack()], context: Context
) -> ToolResult:
    """Get exhaustive item details by ID and type (product, material, or service).

    Returns every field Katana exposes on the item record, plus nested
    ``variants`` (summary), ``configs``, and ``supplier``. The API is
    polymorphic: Product / Material / Service each have their own field
    set, and type-specific fields (``is_producible`` on products, etc.)
    stay ``None`` for the other types.

    Use after search_items. For variant-level detail (barcodes, supplier
    codes, custom fields), follow up with ``get_variant_details``.
    """
    response = await _get_item_impl(request, context)
    return _item_details_to_tool_result(response)


# ============================================================================
# Tool: modify_item — unified modification surface
# ============================================================================


class ItemOperation(StrEnum):
    """Operation names emitted on ActionSpecs by ``modify_item`` /
    ``delete_item`` plan builders."""

    UPDATE_HEADER = "update_header"
    DELETE = "delete"
    ADD_VARIANT = "add_variant"
    UPDATE_VARIANT = "update_variant"
    DELETE_VARIANT = "delete_variant"


# Per-type endpoint routing for header update / get / delete. The variant
# endpoints (``/variant`` family) are shared across types, so they're not
# part of this table.
_TYPE_ENDPOINTS: dict[ItemType, dict[str, Any]] = {
    ItemType.PRODUCT: {
        "get": api_get_product,
        "update": api_update_product,
        "delete": api_delete_product,
        "return_type": Product,
        "update_request": APIUpdateProductRequest,
        "label": "product",
        "web_url_kind": "product",
    },
    ItemType.MATERIAL: {
        "get": api_get_material,
        "update": api_update_material,
        "delete": api_delete_material,
        "return_type": Material,
        "update_request": APIUpdateMaterialRequest,
        "label": "material",
        "web_url_kind": "material",
    },
    ItemType.SERVICE: {
        "get": api_get_service,
        "update": api_update_service,
        "delete": api_delete_service,
        "return_type": Service,
        "update_request": APIUpdateServiceRequest,
        "label": "service",
        # Services have no Katana web page; downstream callers handle a
        # ``None`` web_url_kind by emitting ``katana_url=None``.
        "web_url_kind": None,
    },
}


# Header-patch fields that are valid only for specific types. Used by
# ``ItemHeaderPatch.validate_for_type`` to reject obviously-misrouted
# fields (e.g. ``is_producible`` on a SERVICE) before they reach the API.
_PRODUCT_ONLY_FIELDS = (
    "is_producible",
    "is_purchasable",
    "is_auto_assembly",
    "serial_tracked",
    "operations_in_sequence",
)
_PRODUCT_AND_MATERIAL_FIELDS = (
    "default_supplier_id",
    "batch_tracked",
    "purchase_uom",
    "purchase_uom_conversion_rate",
    "configs",
)
_SERVICE_ONLY_FIELDS = ("sales_price", "default_cost", "sku")


class ItemConfigPatch(BaseModel):
    """A configuration attribute (e.g. ``Size``, ``Teeth``) on a product or material.

    ``configs`` declare the set of attribute *names* a product/material exposes
    and the allowed *values* for each. Variants pin specific values via
    ``config_attributes``. The Katana update endpoint replaces the full
    ``configs`` list at apply time — sending one config entry deletes any
    others not included, so always send the full set.

    ``id`` is only honored for materials (Katana's product-update DTO ignores
    it). When omitted, the API matches existing configs by ``name``.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Config attribute name (e.g. ``Size``).")
    values: list[str] = Field(
        ..., description='Allowed values for this attribute (e.g. ``["S", "M"]``).'
    )
    id: int | None = Field(
        default=None,
        description=(
            "Existing config ID to match (MATERIAL only — products are matched "
            "by ``name`` and ignore ``id``)."
        ),
    )


class VariantConfigAttributePatch(BaseModel):
    """A specific config-attribute value pinned to one variant.

    ``config_name`` must match a config defined on the parent product/material;
    ``config_value`` must be one of that config's allowed values. Sending an
    unknown name or value yields a 422 from Katana.
    """

    model_config = ConfigDict(extra="forbid")

    config_name: str = Field(
        ..., description="Name of the parent's config (e.g. ``Size``)."
    )
    config_value: str = Field(..., description="Value for this variant (e.g. ``M``).")


class ItemHeaderPatch(BaseModel):
    """Header fields to patch on an item.

    The schema is a super-set across all three item types (product / material /
    service); ``ModifyItemRequest`` validates that the supplied fields match
    the chosen ``type`` at runtime. The split is in
    ``_PRODUCT_ONLY_FIELDS`` / ``_PRODUCT_AND_MATERIAL_FIELDS`` /
    ``_SERVICE_ONLY_FIELDS``.
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, description="New item name")
    uom: str | None = Field(default=None, description="New unit of measure")
    category_name: str | None = Field(default=None, description="New category")
    is_sellable: bool | None = Field(default=None)
    is_archived: bool | None = Field(default=None)
    additional_info: str | None = Field(default=None)
    custom_field_collection_id: int | None = Field(default=None)

    # Product + Material only:
    default_supplier_id: int | None = Field(
        default=None,
        description=("New default supplier ID. Look up via `list_suppliers`."),
    )
    batch_tracked: bool | None = Field(default=None)
    purchase_uom: str | None = Field(default=None)
    purchase_uom_conversion_rate: float | None = Field(default=None)
    configs: list[ItemConfigPatch] | None = Field(
        default=None,
        description=(
            "Replace the full set of configuration attributes (variant-defining "
            "axes like ``Size`` / ``Color``). Katana overwrites the existing "
            "list — omit a config and it gets deleted at apply time, so include "
            "every config you want to keep. PRODUCT/MATERIAL only."
        ),
    )

    # Product only:
    is_producible: bool | None = Field(default=None)
    is_purchasable: bool | None = Field(default=None)
    is_auto_assembly: bool | None = Field(default=None)
    serial_tracked: bool | None = Field(default=None)
    operations_in_sequence: bool | None = Field(default=None)

    # Service only:
    sales_price: float | None = Field(default=None)
    default_cost: float | None = Field(default=None)
    sku: str | None = Field(
        default=None,
        description="(SERVICE only) — services carry SKU on the header itself.",
    )


class VariantAdd(BaseModel):
    """A new variant to attach to a product or material.

    Variants are not supported on services — services carry their pricing
    on the item header itself. The dispatcher injects ``product_id`` /
    ``material_id`` based on the parent item type.
    """

    model_config = ConfigDict(extra="forbid")

    sku: str = Field(..., description="Variant SKU")
    sales_price: float | None = Field(default=None)
    purchase_price: float | None = Field(default=None)
    supplier_item_codes: list[str] | None = Field(default=None)
    internal_barcode: str | None = Field(default=None)
    registered_barcode: str | None = Field(default=None)
    lead_time: int | None = Field(default=None)
    minimum_order_quantity: float | None = Field(default=None)
    config_attributes: list[VariantConfigAttributePatch] | None = Field(
        default=None,
        description=(
            "Pin one value per parent config to define this variant. Each "
            "``config_name`` must match a config on the parent and "
            "``config_value`` must be one of that config's allowed values."
        ),
    )


class VariantUpdate(BaseModel):
    """Patch to an existing variant."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Variant ID")
    sku: str | None = Field(default=None)
    sales_price: float | None = Field(default=None)
    purchase_price: float | None = Field(default=None)
    supplier_item_codes: list[str] | None = Field(default=None)
    internal_barcode: str | None = Field(default=None)
    registered_barcode: str | None = Field(default=None)
    lead_time: int | None = Field(default=None)
    minimum_order_quantity: float | None = Field(default=None)
    config_attributes: list[VariantConfigAttributePatch] | None = Field(
        default=None,
        description=(
            "Replace this variant's pinned config-attribute values. The new "
            "list overwrites the existing one at apply time."
        ),
    )


class ModifyItemRequest(ConfirmableRequest):
    """Unified modification request for an item (product / material / service).

    The ``type`` discriminator routes header updates to the matching
    ``products`` / ``materials`` / ``services`` endpoint family. Variant
    sub-payloads route to the shared ``/variant`` family — but only for
    PRODUCT and MATERIAL (services don't expose variant CRUD via that
    endpoint; their pricing lives on the header itself).

    To remove an item entirely, use ``delete_item``.
    """

    id: int = Field(..., description="Item ID (parent product / material / service)")
    type: ItemType = Field(..., description="Item type — drives endpoint routing")
    update_header: ItemHeaderPatch | None = Field(default=None)
    add_variants: list[VariantAdd] | None = Field(default=None)
    update_variants: list[VariantUpdate] | None = Field(default=None)
    delete_variant_ids: list[int] | None = Field(default=None)


class DeleteItemRequest(ConfirmableRequest):
    """Delete an item. Destructive — Katana cascades child variants."""

    id: int = Field(..., description="Item ID to delete")
    type: ItemType = Field(..., description="Item type — drives endpoint routing")


def _validate_header_for_type(patch: ItemHeaderPatch, item_type: ItemType) -> None:
    """Reject obviously-misrouted header fields before they reach the API.

    The API will return a 422 for an invalid field anyway, but a ValueError
    raised in the impl gives the caller a clearer message ("X is not valid
    for SERVICE") and keeps the dispatcher's fail-fast log cleaner.
    """
    set_fields = {k for k, v in patch.model_dump().items() if v is not None}
    invalid: list[tuple[str, str]] = []
    if item_type == ItemType.SERVICE:
        for field in _PRODUCT_ONLY_FIELDS + _PRODUCT_AND_MATERIAL_FIELDS:
            if field in set_fields:
                invalid.append((field, "PRODUCT/MATERIAL only"))
    elif item_type == ItemType.MATERIAL:
        for field in _PRODUCT_ONLY_FIELDS + _SERVICE_ONLY_FIELDS:
            if field in set_fields:
                invalid.append(
                    (
                        field,
                        "PRODUCT-only"
                        if field in _PRODUCT_ONLY_FIELDS
                        else "SERVICE-only",
                    )
                )
    elif item_type == ItemType.PRODUCT:
        for field in _SERVICE_ONLY_FIELDS:
            if field in set_fields:
                invalid.append((field, "SERVICE-only"))

    if invalid:
        details = ", ".join(f"{f} ({reason})" for f, reason in invalid)
        raise ValueError(
            f"Header field(s) not valid for type={item_type.value}: {details}"
        )


def _coerce_product_configs(
    raw: list[dict[str, Any]],
) -> list[APIUpdateProductConfigsItem]:
    """Map ``ItemConfigPatch`` dicts to the product-update attrs class.

    The product DTO accepts only ``name`` and ``values`` — any ``id`` is
    dropped here so callers who include it (legitimately, for materials)
    don't trip ``additionalProperties: false`` on the wire.
    """
    return [
        APIUpdateProductConfigsItem(name=c["name"], values=list(c["values"]))
        for c in raw
    ]


def _coerce_material_configs(
    raw: list[dict[str, Any]],
) -> list[APIUpdateMaterialConfigsItem]:
    """Map ``ItemConfigPatch`` dicts to the material-update attrs class.

    Materials accept the optional ``id`` for matching existing configs.
    """
    return [
        APIUpdateMaterialConfigsItem(
            name=c["name"],
            values=list(c["values"]),
            id=to_unset(c.get("id")),
        )
        for c in raw
    ]


def coerce_variant_config_attributes(
    raw: list[dict[str, Any]],
    item_cls: type[APICreateVariantConfigItem] | type[APIUpdateVariantConfigItem],
) -> list[Any]:
    """Map ``VariantConfigAttributePatch`` dicts to the create- or update-side
    attrs class. Both target classes share the ``config_name`` /
    ``config_value`` shape — ``item_cls`` chooses which one fits the
    sibling Update*Request."""
    return [
        item_cls(config_name=c["config_name"], config_value=c["config_value"])
        for c in raw
    ]


def _build_update_header_request(
    patch: ItemHeaderPatch, item_type: ItemType, existing_item: Any | None = None
) -> Any:
    """Map an ItemHeaderPatch to the right Update*Request attrs class.

    Each type has a different field set; ``unset_dict`` filters down to
    the actual fields the API accepts after we've validated routing.
    ``additional_info`` is echoed via :func:`patch_additional_info` so
    Katana's wipe-on-omit doesn't destroy item notes during a header
    rename (see its docstring for the full workaround story).
    """
    request_cls = _TYPE_ENDPOINTS[item_type]["update_request"]
    transforms: dict[str, Any] = {}
    if item_type == ItemType.PRODUCT:
        exclude = _SERVICE_ONLY_FIELDS
        transforms["configs"] = _coerce_product_configs
    elif item_type == ItemType.MATERIAL:
        exclude = _PRODUCT_ONLY_FIELDS + _SERVICE_ONLY_FIELDS
        transforms["configs"] = _coerce_material_configs
    else:
        exclude = _PRODUCT_ONLY_FIELDS + _PRODUCT_AND_MATERIAL_FIELDS
    kwargs = unset_dict(patch, exclude=exclude, transforms=transforms)
    kwargs["additional_info"] = patch_additional_info(
        patch.additional_info,
        existing_item.additional_info if existing_item is not None else UNSET,
    )
    return request_cls(**kwargs)


def _build_create_variant_request(
    parent_id: int, item_type: ItemType, variant: VariantAdd
) -> APICreateVariantRequest:
    """Build a CreateVariantRequest with parent_id wired into the right slot.

    The Katana ``/variant`` POST takes ``product_id`` *or* ``material_id``
    on the request body to identify the parent. ``modify_item`` infers
    that from the item ``type`` so the caller doesn't have to.
    """
    extra: dict[str, Any] = {}
    if item_type == ItemType.PRODUCT:
        extra["product_id"] = parent_id
    elif item_type == ItemType.MATERIAL:
        extra["material_id"] = parent_id
    kwargs = unset_dict(
        variant,
        transforms={
            "config_attributes": lambda raw: coerce_variant_config_attributes(
                raw, APICreateVariantConfigItem
            ),
        },
    )
    return APICreateVariantRequest(**kwargs, **extra)


def _build_update_variant_request(patch: VariantUpdate) -> APIUpdateVariantRequest:
    kwargs = unset_dict(
        patch,
        exclude=("id",),
        transforms={
            "config_attributes": lambda raw: coerce_variant_config_attributes(
                raw, APIUpdateVariantConfigItem
            ),
        },
    )
    return APIUpdateVariantRequest(**kwargs)


async def _fetch_item_for_diff(services: Any, item_id: int, item_type: ItemType) -> Any:
    """Best-effort fetch of the parent item for diff context."""
    cfg = _TYPE_ENDPOINTS[item_type]
    return await safe_fetch_for_diff(
        cfg["get"],
        services,
        item_id,
        return_type=cfg["return_type"],
        label=cfg["label"],
    )


async def _fetch_variant_for_diff(services: Any, variant_id: int) -> Variant | None:
    return await safe_fetch_for_diff(
        api_get_variant,
        services,
        variant_id,
        return_type=Variant,
        label="variant",
    )


async def _invalidate_item_cache(_services: Any, _item_type: ItemType) -> None:
    """No-op kept for call-site compatibility.

    Pre-#472 this marked the per-type entity row and the variants table
    dirty in the legacy ``CatalogCache``. The typed cache (#342) pulls
    incremental deltas via ``updated_at_min`` on every
    ``@cache_read``-decorated call, so the next ``search_items`` /
    ``get_variant_details`` sees the new row without a manual dirty bit.
    Phase D folded the legacy cache out, leaving this helper as a
    no-op rather than ripping it out — it's still a useful seam if
    we ever need to add a cache hook back at the modify-apply path.
    """
    return None


async def _modify_item_impl(
    request: ModifyItemRequest, context: Context
) -> ModificationResponse:
    """Build the action plan for an item modify and either preview or execute.

    Type discriminator routes header endpoints; variant sub-payloads route
    to the shared ``/variant`` family. SERVICE rejects variant CRUD up
    front (Katana doesn't expose ``/variant`` POST/PATCH/DELETE for
    services).
    """
    services = get_services(context)

    # ``type`` is a routing discriminator, not a sub-payload — exclude it from
    # the "is anything set?" check so a request with only ``type`` set is
    # still rejected.
    if not has_any_subpayload(request, exclude=("id", "type", "preview")):
        raise ValueError(
            "At least one sub-payload must be set: update_header, "
            "add_variants, update_variants, or delete_variant_ids. "
            "To remove the item entirely, use delete_item."
        )

    if request.type == ItemType.SERVICE and (
        request.add_variants or request.update_variants or request.delete_variant_ids
    ):
        raise ValueError(
            "Variant CRUD is not supported for SERVICE items — services "
            "carry pricing on the header itself (sales_price, default_cost, sku)."
        )

    if request.update_header is not None:
        _validate_header_for_type(request.update_header, request.type)

    cfg = _TYPE_ENDPOINTS[request.type]
    existing_item = await _fetch_item_for_diff(services, request.id, request.type)

    plan: list[ActionSpec] = []

    if request.update_header is not None:
        diff = compute_field_diff(
            existing_item, request.update_header, unknown_prior=existing_item is None
        )
        plan.append(
            ActionSpec(
                operation=ItemOperation.UPDATE_HEADER,
                target_id=request.id,
                diff=diff,
                apply=make_patch_apply(
                    cfg["update"],
                    services,
                    request.id,
                    _build_update_header_request(
                        request.update_header, request.type, existing_item
                    ),
                    return_type=cfg["return_type"],
                ),
                verify=make_response_verifier(diff),
            )
        )

    plan.extend(
        plan_creates(
            request.add_variants,
            ItemOperation.ADD_VARIANT,
            lambda variant: _build_create_variant_request(
                request.id, request.type, variant
            ),
            lambda body: make_post_apply(
                api_create_variant, services, body, return_type=Variant
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_variants,
            ItemOperation.UPDATE_VARIANT,
            lambda vid: _fetch_variant_for_diff(services, vid),
            _build_update_variant_request,
            lambda vid, body: make_patch_apply(
                api_update_variant, services, vid, body, return_type=Variant
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_variant_ids,
            ItemOperation.DELETE_VARIANT,
            lambda vid: make_delete_apply(api_delete_variant, services, vid),
        )
    )

    response = await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type=request.type.value,
            entity_label=f"{cfg['label']} {request.id}",
            tool_name="modify_item",
        ),
        web_url_kind=cfg["web_url_kind"],
        existing=existing_item,
        plan=plan,
        # ``_fetch_item_attrs`` calls ``unwrap()`` directly and raises on
        # any 4xx/5xx (unlike ``safe_fetch_for_diff`` used by other modify
        # tools). Wrap in a try/except so the ``refetch_for_merge``
        # contract — ``returns Any | None`` — holds: a refetch failure
        # returns ``None`` and the dispatcher's ``_post_apply_cache_merge``
        # short-circuits cleanly instead of unwinding through the outer
        # best-effort handler with a misleading traceback. Same data shape
        # as before — ``extend=[SUPPLIER]`` is preserved.
        cache_merge=CacheMerge(
            cache=services.typed_cache,
            refetch_for_merge=lambda eid: _safe_fetch_item_attrs(
                services, eid, request.type
            ),
        ),
    )

    if not request.preview:
        await _invalidate_item_cache(services, request.type)

    return response


@observe_tool
@unpack_pydantic_params
async def modify_item(
    request: Annotated[ModifyItemRequest, Unpack()], context: Context
) -> ToolResult:
    """Modify an item — unified surface across header + variant CRUD.

    The required ``type`` discriminator (PRODUCT / MATERIAL / SERVICE)
    routes header updates to the matching API endpoint family. Variant
    sub-payloads (``add_variants`` / ``update_variants`` /
    ``delete_variant_ids``) route to the shared ``/variant`` family —
    available for PRODUCT and MATERIAL only; services carry pricing on
    the header itself (``sales_price``, ``default_cost``, ``sku``).

    Sub-payloads (any subset, all optional):

    - ``update_header`` — patch header fields. Field set is type-specific:
      ``is_producible`` etc. are PRODUCT-only, ``default_supplier_id``
      etc. are PRODUCT/MATERIAL, ``sales_price`` etc. are SERVICE-only.
      ``is_archived`` is shared across all three types and is the
      archive/unarchive lever (Katana has no dedicated archive endpoint).
      Misrouted fields fail fast with a clear error.
    - ``add_variants`` — POST /variant. Parent ``product_id`` /
      ``material_id`` is injected from the request's ``type``.
    - ``update_variants`` — PATCH /variant/{id}.
    - ``delete_variant_ids`` — DELETE /variant/{id}.

    Archive / unarchive: send ``{"update_header": {"is_archived": true}}`` to
    archive, ``{"update_header": {"is_archived": false}}`` to unarchive.
    Archived items are hidden from ``search_items`` by default; pass
    ``include_archived=true`` on that call to find them.

    To remove an item entirely, use the sibling ``delete_item`` tool.

    Two-step flow: ``preview=true`` (default) returns a per-action preview;
    ``preview=false`` executes the plan in canonical order. Fail-fast on
    error.
    """
    response = await _modify_item_impl(request, context)
    return to_tool_result(response, confirm_request=request, confirm_tool="modify_item")


# ============================================================================
# Tool: delete_item
# ============================================================================


async def _delete_item_impl(
    request: DeleteItemRequest, context: Context
) -> ModificationResponse:
    """One-action plan that removes the item. Katana cascades child variants."""
    cfg = _TYPE_ENDPOINTS[request.type]
    services = get_services(context)

    response = await run_delete_plan(
        request=request,
        services=services,
        entity_type=request.type.value,
        entity_label=f"{cfg['label']} {request.id}",
        web_url_kind=cfg["web_url_kind"],
        fetcher=lambda svc, eid: _fetch_item_for_diff(svc, eid, request.type),
        delete_endpoint=cfg["delete"],
        operation=ItemOperation.DELETE,
    )

    if not request.preview:
        await _invalidate_item_cache(services, request.type)

    return response


@observe_tool
@unpack_pydantic_params
async def delete_item(
    request: Annotated[DeleteItemRequest, Unpack()], context: Context
) -> ToolResult:
    """Permanently delete an item (product, material, or service) from Katana.

    The required ``type`` discriminator routes the delete to the matching
    endpoint family. Destructive — Katana cascades the delete to child
    variants server-side. The response carries a ``prior_state`` snapshot
    for manual revert.
    """
    response = await _delete_item_impl(request, context)
    return to_tool_result(response, confirm_request=request, confirm_tool="delete_item")


# ============================================================================
# Tool 6: get_variant_details
# ============================================================================


class GetVariantDetailsRequest(BaseModel):
    """Request to get variant details by SKU(s) or variant ID(s).

    Accepts a single sku/variant_id OR a list (skus/variant_ids) for batch lookups.
    """

    model_config = ConfigDict(extra="forbid")

    sku: str | None = Field(
        default=None,
        description="Single SKU to look up (exact case-insensitive match)",
    )
    variant_id: int | None = Field(
        default=None,
        description="Single variant ID to look up directly",
    )
    skus: CoercedStrListOpt = Field(
        default=None,
        description=(
            'Batch lookup: JSON array of SKUs, e.g. ["WS74001", "WS74002"]. '
            "Each SKU is matched case-insensitively."
        ),
    )
    variant_ids: CoercedIntListOpt = Field(
        default=None,
        description="Batch lookup: JSON array of variant IDs, e.g. [12345, 67890].",
    )


class VariantDetailsResponse(BaseModel):
    """Full variant details. Exhaustive — every field Katana exposes on the
    ``Variant`` attrs model is surfaced, including nested configuration
    attributes and custom fields, so callers don't need follow-up lookups.

    A handful of fields (``uom``, ``default_supplier_*``, ``is_batch_tracked``)
    live on the parent product/material rather than on the variant attrs
    model. The impl resolves the parent from the cache and lifts these
    fields onto the variant response so a single ``get_variant_details``
    call surfaces every fact a caller typically needs to act on.
    """

    # Core fields
    id: int
    sku: str
    name: str
    """Display-format variant name. In practice this is the same value
    as :attr:`display_name` below — ``_dict_to_variant_details``
    populates both from the canonical formula. Preserved as a separate
    field so wire-level consumers that historically read ``name`` keep
    working; new consumers should prefer :attr:`display_name` for
    semantic clarity. The raw Katana ``variant.name`` attribute is not
    surfaced separately on this response — every code path uses the
    formatted display name.
    """
    display_name: str = ""
    """Katana-UI-format human-readable name: ``"{parent_name} / {config1} / {config2}"``.

    Built via :func:`katana_public_api_client.domain.variant.build_variant_display_name`
    so it stays consistent with the typed-cache ``CachedVariant.display_name``
    column and the ``KatanaVariant.get_display_name`` domain method.
    This is the canonical title field for UI rendering. The legacy
    ``name`` field above carries the same value today; prefer this one.
    """

    # Pricing
    sales_price: float | None = None
    purchase_price: float | None = None

    # Classification
    type: str | None = None
    product_id: int | None = None
    material_id: int | None = None
    product_or_material_name: str | None = None

    # Parent-item context (lifted from the parent product/material —
    # variants don't carry these on the attrs model directly)
    uom: str | None = None
    default_supplier_id: int | None = None
    default_supplier_name: str | None = None
    is_batch_tracked: bool | None = None
    purchase_uom: str | None = None
    purchase_uom_conversion_rate: float | None = None

    # Deep-link to the parent product or material — variants don't have
    # their own page in Katana's web app, so callers click through to the
    # parent record.
    katana_url: str | None = None

    # Barcode & Inventory
    internal_barcode: str | None = None
    registered_barcode: str | None = None
    supplier_item_codes: list[str] = Field(default_factory=list)

    # Ordering
    lead_time: int | None = None
    minimum_order_quantity: float | None = None

    # Configuration & Custom Fields
    config_attributes: list[dict[str, str]] = Field(default_factory=list)
    custom_fields: list[dict[str, str]] = Field(default_factory=list)

    # Metadata
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


class VariantNotFound(BaseModel):
    """Identifier for a variant that was requested but couldn't be resolved.

    Exactly one of ``sku`` / ``variant_id`` is set, matching the form the
    caller used in the request. Surfaced from
    :func:`_get_variant_details_impl` so batch callers can see the gaps
    without parsing exception text. The XOR is enforced at validation
    time so invalid shapes (both set, both unset) can't leak into the
    JSON envelope — every miss must carry a single identifying field so
    callers can match it back to the request.
    """

    sku: str | None = None
    variant_id: int | None = None

    @model_validator(mode="after")
    def _check_exactly_one_identifier(self) -> VariantNotFound:
        if (self.sku is None) == (self.variant_id is None):
            raise ValueError(
                "VariantNotFound requires exactly one of 'sku' or 'variant_id'; "
                f"got sku={self.sku!r}, variant_id={self.variant_id!r}"
            )
        return self


class GetVariantDetailsResult(BaseModel):
    """Partial-result envelope for variant lookups.

    Splits hits from misses so a batch with one bad SKU still returns the
    rest of the batch. The singular convenience path (a request with a
    single ``sku=`` / ``variant_id=``) keeps raising ``ValueError`` for a
    clean "that one variant doesn't exist" UX — only the batch path
    (``skus=[...]`` / ``variant_ids=[...]`` or any mixed form) lands here
    and never short-circuits. See issue #617.
    """

    found: list[VariantDetailsResponse] = Field(default_factory=list)
    not_found: list[VariantNotFound] = Field(default_factory=list)


def _iso_or_none(value: Any) -> str | None:
    """Return an ISO-8601 string for a datetime-or-str value, else None."""
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _dict_to_variant_details(
    v: Any,
    *,
    parent: Any | None = None,
    supplier: Any | None = None,
) -> VariantDetailsResponse:
    """Build a VariantDetailsResponse from a variant cache row or attrs model.

    Surfaces every field the generated ``Variant`` attrs model exposes
    plus the parent-derived context (``uom``, ``default_supplier_*``,
    ``is_batch_tracked``) when ``parent`` and/or ``supplier`` rows are
    supplied. Both are optional; missing parents/suppliers (cold cache,
    miss) gracefully degrade to ``None`` for those fields.

    Accepts either a ``CachedVariant`` SQLModel (the cache hit path)
    or a generated ``Variant`` attrs model (the API-fallback path)
    via ``_attr``, which unwraps ``UNSET`` for the attrs side and
    returns plain attributes for the cache side.

    The ``config_attributes`` / ``custom_fields`` fields come back as
    typed pydantic objects on the cache side (``ConfigAttribute`` /
    ``CustomField``); we ``model_dump()`` them so the response remains
    plain-dict-shaped for JSON consumers — same wire shape the legacy
    cache emitted via ``json_columns``.
    """
    product_id = _attr(v, "product_id")
    material_id = _attr(v, "material_id")
    # Variants don't have their own page in Katana; link to whichever
    # parent (product or material) actually owns this variant. Picking
    # by which field is non-null (vs `or`) keeps the kind correct if
    # the URL paths ever diverge.
    parent_url = katana_web_url("product", product_id) or katana_web_url(
        "material", material_id
    )
    # Cache rows / dicts use ``type``; the generated attrs ``Variant``
    # uses ``type_`` (trailing underscore — Python keyword collision in
    # the OpenAPI generator's name-mangling). Read both so cache-hit and
    # API-fallback paths produce the same response shape; otherwise the
    # API-fallback response would carry ``type=None`` and the Prefab UI
    # would silently drop the type badge.
    type_val = _attr(v, "type") or _attr(v, "type_")
    type_str = type_val.value if hasattr(type_val, "value") else type_val

    def _dump_list(items: Any) -> list[Any]:
        # Cache rows carry pydantic items (``ConfigAttribute`` /
        # ``CustomField``); API-fallback variants carry attrs items
        # (``VariantConfigAttributesType0Item`` /
        # ``VariantCustomFieldsType0Item`` — the generator suffix
        # ``Type0`` reflects the array-side of the nullable union
        # type, see #727). Both need to land as plain dicts on the
        # response so the pydantic ``VariantDetailsResponse`` validator
        # accepts them — attrs models expose ``to_dict()``, pydantic
        # models expose ``model_dump()``.
        if not items:
            return []
        return [
            item.model_dump()
            if hasattr(item, "model_dump")
            else item.to_dict()
            if hasattr(item, "to_dict")
            else item
            for item in items
        ]

    parent_name_value = _attr(v, "parent_name") or _attr(parent, "name")
    sku_value = _attr(v, "sku") or ""
    # ``display_name`` from the cache row is already pre-computed via the
    # variant postprocess hook (which itself delegates to
    # ``build_variant_display_name``). For the API-fallback path the cache
    # row's field is absent — compute fresh from parent + configs so the
    # response always carries a canonical display name regardless of
    # which code path produced ``v``.
    display_name_value = _attr(v, "display_name") or build_variant_display_name(
        parent_name_value,
        _attr(v, "config_attributes") or [],
        sku_value,
    )
    return VariantDetailsResponse(
        id=_attr(v, "id"),
        sku=sku_value,
        name=display_name_value or sku_value,
        display_name=display_name_value,
        sales_price=_attr(v, "sales_price"),
        purchase_price=_attr(v, "purchase_price"),
        type=type_str,
        product_id=product_id,
        material_id=material_id,
        product_or_material_name=parent_name_value,
        uom=_attr(parent, "uom"),
        default_supplier_id=_attr(parent, "default_supplier_id"),
        default_supplier_name=_attr(supplier, "name"),
        is_batch_tracked=_attr(parent, "batch_tracked"),
        purchase_uom=_attr(parent, "purchase_uom"),
        purchase_uom_conversion_rate=_attr(parent, "purchase_uom_conversion_rate"),
        katana_url=parent_url,
        internal_barcode=_attr(v, "internal_barcode"),
        registered_barcode=_attr(v, "registered_barcode"),
        supplier_item_codes=_attr(v, "supplier_item_codes") or [],
        lead_time=_attr(v, "lead_time"),
        minimum_order_quantity=_attr(v, "minimum_order_quantity"),
        config_attributes=_dump_list(_attr(v, "config_attributes")),
        custom_fields=_dump_list(_attr(v, "custom_fields")),
        created_at=_iso_or_none(_attr(v, "created_at")),
        updated_at=_iso_or_none(_attr(v, "updated_at")),
        deleted_at=_iso_or_none(_attr(v, "deleted_at")),
    )


async def _enrich_variants_with_parent(
    services: Any, variants: list[Any]
) -> tuple[dict[int, Any], dict[int, Any], dict[int, Any]]:
    """Bulk-fetch parent products/materials and default suppliers for a
    set of variants. Returns ``(products_by_id, materials_by_id,
    supplier_by_id)`` — separate maps per entity type so callers can
    select the correct parent based on whether the variant carries
    ``product_id`` or ``material_id``.

    Product and material IDs are NOT guaranteed disjoint (the cache
    used to key rows by ``(entity_type, id)``; the typed cache keeps
    the same shape via per-class tables), so merging into a single
    map keyed only by numeric ID would mis-associate parents on
    collision — see CLAUDE.md "Cache IDs are not globally unique".

    Splits parent IDs by entity type and uses ``get_many_by_ids`` per
    type so we make at most three cache queries total
    (parents-product, parents-material, suppliers) regardless of how
    many variants are in the input. Passes ``include_archived=True``
    /``include_deleted=True`` so direct-lookup (variant → parent)
    enrichment doesn't drop rows for archived parents — the
    ``is_archived`` flag still surfaces on the response, but the
    parent's ``uom`` / ``default_supplier_*`` data still loads.
    """
    product_ids = {pid for v in variants if (pid := _attr(v, "product_id"))}
    material_ids = {mid for v in variants if (mid := _attr(v, "material_id"))}
    catalog = services.typed_cache.catalog
    products, materials = await asyncio.gather(
        catalog.get_many_by_ids(
            CachedProduct, product_ids, include_archived=True, include_deleted=True
        ),
        catalog.get_many_by_ids(
            CachedMaterial, material_ids, include_archived=True, include_deleted=True
        ),
    )
    # Pull supplier IDs from both parent rows, then bulk-resolve
    # supplier names — usually a small unique set even for big variant lists.
    supplier_ids = {
        sid
        for p in (*products.values(), *materials.values())
        if (sid := _attr(p, "default_supplier_id"))
    }
    supplier_by_id = await catalog.get_many_by_ids(
        CachedSupplier, supplier_ids, include_deleted=True
    )
    return products, materials, supplier_by_id


async def _fetch_variant_by_id(services: Any, variant_id: int) -> Any | None:
    """Look up a variant by ID — cache first, then API fallback.

    Returns either a ``CachedVariant`` (cache hit) or a ``Variant``
    attrs model (API fallback), or ``None`` if neither path turned
    up the row. Both shapes share the field names callers read
    (``id``, ``sku``, ``product_id``, ``material_id``, ...), so
    callers use ``_attr`` to access them uniformly.

    Uses ``raise_on_error=False`` so a 404 (or an ErrorResponse body)
    becomes ``None`` instead of a raw ``APIError``, which is what
    callers expect as the "not found" sentinel. Passes
    ``include_archived=True`` / ``include_deleted=True`` to the
    cache lookup so direct-lookup parity matches the legacy cache
    (every row regardless of soft-state).
    """
    v = await services.typed_cache.catalog.get_by_id(
        CachedVariant, variant_id, include_archived=True, include_deleted=True
    )
    if v is not None:
        return v
    # Cache miss — fetch from API
    from katana_public_api_client.api.variant import get_variant
    from katana_public_api_client.models import ErrorResponse
    from katana_public_api_client.utils import unwrap

    response = await get_variant.asyncio_detailed(id=variant_id, client=services.client)
    variant_obj = unwrap(response, raise_on_error=False)
    if variant_obj is None or isinstance(variant_obj, ErrorResponse):
        return None
    return variant_obj


def _collect_variant_identifiers(
    request: GetVariantDetailsRequest,
) -> tuple[list[str], list[int]]:
    """Flatten the request's singular + plural identifier fields into
    a single ``(skus, variant_ids)`` pair, validating that at least one
    identifier was provided and that no SKU is blank."""
    skus: list[str] = []
    variant_ids: list[int] = []

    if request.sku is not None:
        # Validate explicit single SKU (even empty string)
        if not request.sku.strip():
            raise ValueError("SKU cannot be empty")
        skus.append(request.sku)
    if request.skus:
        skus.extend(request.skus)
    if request.variant_id is not None:
        variant_ids.append(request.variant_id)
    if request.variant_ids:
        variant_ids.extend(request.variant_ids)

    if not skus and not variant_ids:
        raise ValueError(
            "Must provide at least one of: sku, variant_id, skus, variant_ids"
        )

    sku_cleaned = [s.strip() for s in skus]
    if any(not clean for clean in sku_cleaned):
        raise ValueError("SKU cannot be empty")

    return sku_cleaned, variant_ids


def _is_singular_request(request: GetVariantDetailsRequest) -> bool:
    """True when the request carries exactly one identifier via the
    scalar ``sku=`` / ``variant_id=`` field, with no plural list. The
    singular path raises on a miss; the batch path returns it in
    ``not_found``."""
    return (
        not request.skus
        and not request.variant_ids
        and (request.sku is not None) ^ (request.variant_id is not None)
    )


def _partition_variant_lookups(
    *,
    sku_cleaned: list[str],
    sku_variants: list[Any | None],
    variant_ids: list[int],
    id_variants: list[Any | None],
    is_singular_request: bool,
) -> tuple[list[Any], list[VariantNotFound]]:
    """Split parallel-lookup results into hits and misses. In singular
    mode, the first miss raises; in batch mode, misses accumulate into
    ``not_found`` and processing continues."""
    hits: list[Any] = []
    not_found: list[VariantNotFound] = []
    for sku, v in zip(sku_cleaned, sku_variants, strict=True):
        if v is None:
            if is_singular_request:
                raise ValueError(f"Variant with SKU '{sku}' not found")
            not_found.append(VariantNotFound(sku=sku))
            continue
        hits.append(v)
    for variant_id, v in zip(variant_ids, id_variants, strict=True):
        if v is None:
            if is_singular_request:
                raise ValueError(f"Variant ID {variant_id} not found")
            not_found.append(VariantNotFound(variant_id=variant_id))
            continue
        hits.append(v)
    return hits, not_found


@cache_read(
    CachedVariant,
    CachedProduct,
    CachedMaterial,
    CachedSupplier,
)
async def _get_variant_details_impl(
    request: GetVariantDetailsRequest, context: Context
) -> GetVariantDetailsResult:
    """Look up one or more variants by SKU(s) or variant ID(s).

    Returns a :class:`GetVariantDetailsResult` with hits in ``found`` and
    misses in ``not_found``. The singular convenience path (the request
    carries exactly one identifier via ``sku=`` or ``variant_id=``, with
    no plural list) keeps raising ``ValueError`` on a miss so the
    "that one variant doesn't exist" UX stays clean. The batch path —
    ``skus=[...]`` / ``variant_ids=[...]`` or any mixed form — never
    short-circuits, so a single bad SKU can't kill an otherwise-good
    batch (#617).
    """
    sku_cleaned, variant_ids = _collect_variant_identifiers(request)
    is_singular_request = _is_singular_request(request)

    services = get_services(context)
    catalog = services.typed_cache.catalog

    # Parallelize both groups of lookups. Direct-lookup parity with the
    # legacy cache: include archived/deleted variants so the user can
    # still inspect rows they're cleaning up.
    sku_variants, id_variants = await asyncio.gather(
        asyncio.gather(
            *(
                catalog.get_by_sku(s, include_archived=True, include_deleted=True)
                for s in sku_cleaned
            )
        ),
        asyncio.gather(*(_fetch_variant_by_id(services, v) for v in variant_ids)),
    )

    hits, not_found = _partition_variant_lookups(
        sku_cleaned=sku_cleaned,
        sku_variants=list(sku_variants),
        variant_ids=variant_ids,
        id_variants=list(id_variants),
        is_singular_request=is_singular_request,
    )

    # Bulk-fetch parents + suppliers once for the whole batch so the
    # response includes UoM, default supplier name, and batch-tracked
    # status without a per-variant follow-up call (#538).
    products, materials, supplier_by_id = await _enrich_variants_with_parent(
        services, hits
    )
    found: list[VariantDetailsResponse] = []
    for v in hits:
        # Pick the parent map by which ID the variant carries — product
        # and material IDs may collide, so a merged map would mis-attach.
        product_id = _attr(v, "product_id")
        material_id = _attr(v, "material_id")
        if product_id:
            parent = products.get(product_id)
        elif material_id:
            parent = materials.get(material_id)
        else:
            parent = None
        sup_id = _attr(parent, "default_supplier_id")
        supplier = supplier_by_id.get(sup_id) if sup_id else None
        found.append(_dict_to_variant_details(v, parent=parent, supplier=supplier))

    return GetVariantDetailsResult(found=found, not_found=not_found)


@observe_tool
@unpack_pydantic_params
async def get_variant_details(
    request: Annotated[GetVariantDetailsRequest, Unpack()], context: Context
) -> ToolResult:
    """Get comprehensive variant details by SKU(s) or variant ID(s).

    Pass one or more values via ``skus`` / ``variant_ids`` (or the singular
    ``sku`` / ``variant_id``). Response is always the JSON
    ``{variants: [...], not_found: [...]}`` envelope for every request shape
    (single OR batch). When exactly one variant resolves and there are no
    misses, a rich Prefab detail card is additionally attached via
    ``structured_content`` for UI hosts. Batching N lookups in one call beats
    N separate invocations.

    Returns pricing, barcodes, supplier codes, and more.

    Use after search_items, or pass variant IDs from other sources (PO line
    items, MO recipe rows) to resolve them to SKUs and full details.

    Tries the cache first; falls back to the API for variant IDs not in cache.
    For a singular request (one ``sku=`` or ``variant_id=``), raises
    ``ValueError`` if the variant isn't found. For a batch request
    (``skus=[...]`` / ``variant_ids=[...]`` or mixed), returns the variants
    that resolved plus a ``not_found`` list of the misses — a single bad
    identifier never kills the whole batch (#617).
    """
    result = await _get_variant_details_impl(request, context)
    found = result.found
    not_found = result.not_found

    # JSON ``content`` is the stable contract: the ``{variants, not_found}``
    # envelope is returned for every request shape — single OR batch — so
    # programmatic consumers see one parseable shape (#567 — no per-tool
    # markdown). ``structured_content`` then differs by shape: a Prefab card
    # for single requests (see below), or the envelope dict for batch.
    # Pre-#567 the format="json" branch already returned this envelope; the
    # single-item bare-VariantDetailsResponse shape was markdown-only.
    import json as _json

    payload = {
        "variants": [r.model_dump(mode="json") for r in found],
        "not_found": [n.model_dump(mode="json", exclude_none=True) for n in not_found],
    }
    content = _json.dumps(payload, indent=2, default=str)

    # Single-variant request → rich Prefab card alongside the envelope.
    # Treat a single-element batch list (skus=[X] or variant_ids=[X]) the
    # same as the singular form to honor the docstring's "single item"
    # promise — but only when there are no misses; with misses we fall
    # through to the bare envelope so the ``not_found`` array still
    # surfaces in structured_content without a Prefab card stealing
    # the slot.
    is_single = (
        len(found) == 1
        and not not_found
        and (
            request.sku is not None
            or request.variant_id is not None
            or len(request.skus or []) == 1
            or len(request.variant_ids or []) == 1
        )
    )
    if is_single:
        from katana_mcp.tools.prefab_ui import build_variant_details_ui

        ui = build_variant_details_ui(found[0].model_dump())
        return ToolResult(content=content, structured_content=ui)

    return ToolResult(content=content, structured_content=payload)


def register_tools(mcp: FastMCP) -> None:
    """Register all item tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    from mcp.types import ToolAnnotations

    from katana_mcp.tools.prefab_ui import register_preview_tool

    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
    _create = ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, openWorldHint=True
    )
    _modify = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )
    _destructive = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )

    mcp.tool(tags={"catalog", "read"}, annotations=_read, meta=UI_META)(search_items)
    # ``create_item`` does not currently expose preview→apply, so it
    # registers as a plain write tool. If its request grows a ``preview``
    # field, switch to ``register_preview_tool``.
    mcp.tool(tags={"catalog", "write"}, annotations=_create, meta=UI_META)(create_item)
    mcp.tool(tags={"catalog", "read"}, annotations=_read, meta=UI_META)(get_item)
    register_preview_tool(
        mcp,
        modify_item,
        tags={"catalog", "write"},
        annotations=_modify,
        meta=UI_META,
        direct=True,
    )
    register_preview_tool(
        mcp,
        delete_item,
        tags={"catalog", "write", "destructive"},
        annotations=_destructive,
        meta=UI_META,
        direct=True,
    )
    mcp.tool(tags={"catalog", "read"}, annotations=_read, meta=UI_META)(
        get_variant_details
    )
