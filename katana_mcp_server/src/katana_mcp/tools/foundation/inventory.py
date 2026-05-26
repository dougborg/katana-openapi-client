"""Inventory management tools for Katana MCP Server.

Foundation tools for checking stock levels, monitoring low stock,
and managing inventory operations.
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from itertools import batched
from typing import Annotated, Any, Literal, NamedTuple

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools._modification import WireDatetime, patch_additional_info
from katana_mcp.tools.decorators import cache_read
from katana_mcp.tools.list_coercion import CoercedIntListOpt, CoercedStrIntList
from katana_mcp.tools.tool_result_utils import (
    UI_META,
    PaginationMeta,
    apply_date_window_filters,
    iso_or_none,
    make_json_result,
    make_tool_result,
    naive_utc,
    parse_iso_datetime,
    parse_request_dates,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import katana_web_url
from katana_public_api_client.api.stock_adjustment import get_all_stock_adjustments
from katana_public_api_client.client_types import UNSET, Unset
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models.get_all_inventory_movements_resource_type import (
    GetAllInventoryMovementsResourceType,
)
from katana_public_api_client.models_pydantic._generated import (
    CachedLocation,
    CachedMaterial,
    CachedProduct,
    CachedSupplier,
    CachedVariant,
)
from katana_public_api_client.utils import unwrap_data

logger = get_logger(__name__)


def _iso_str(val: Any) -> str:
    """Return ``val.isoformat()`` when possible, else ``str(val)``.

    The Katana attrs models type ``movement_date`` / ``created_at`` /
    ``updated_at`` as ``datetime``, but unit tests fixture them as strings
    via ``MagicMock`` — accept both so call sites stay shape-agnostic.
    """
    return val.isoformat() if hasattr(val, "isoformat") else str(val)


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    """Read ``name`` from a cache row, attrs model, OR dict uniformly.

    Cached SQLModel rows expose plain attributes; attrs models use the
    ``UNSET`` sentinel for missing optional fields; tests occasionally
    fixture in raw dicts (the legacy cache shape) — accept all three
    so call sites stay agnostic to which side filled the slot.
    Used by the variant-lookup paths in :mod:`inventory` and
    :mod:`items` after the #472 Phase D migration.
    """
    if obj is None:
        return default
    if isinstance(obj, dict):
        val = obj.get(name, default)
    else:
        val = getattr(obj, name, default)
    return default if val is UNSET else val


# ============================================================================
# Tool 1: check_inventory
# ============================================================================


class CheckInventoryRequest(BaseModel):
    """Request model for checking inventory."""

    model_config = ConfigDict(extra="forbid")

    skus_or_variant_ids: CoercedStrIntList = Field(
        ...,
        min_length=1,
        description=(
            "JSON array of SKUs (strings) or variant IDs (integers) — mix freely. "
            'E.g., ["WS74001", 12345] or ["WS74001", "WS74002"]. '
            "Response is always the JSON `{items: [...]}` envelope (single OR batch); "
            "a Prefab stock card is attached for UI hosts on every shape. "
            "Batching N items in a single call beats N separate invocations. "
            "Output order matches input order."
        ),
    )
    location_id: int | None = Field(
        default=None,
        description=(
            "Filter to a single warehouse/facility. When set, the response "
            "totals and `by_location` only include this location. "
            "Look up via `list_locations`."
        ),
    )
    include_archived: bool = Field(
        default=False,
        description=(
            "Include archived rows across both surfaces of this tool: "
            "(1) variants whose parent product/material is archived (the "
            "identifier-resolution side), and (2) per-location inventory "
            "rows individually archived at a single warehouse (threaded to "
            "`/inventory` and surfaced via `LocationStock.is_archived`). "
            "Default `False` returns only active rows; on a duplicate SKU, "
            "the live row always wins. Set `True` for cleanup workflows."
        ),
    )
    include_deleted: bool = Field(
        default=False,
        description=(
            "Include soft-deleted variants on the identifier-resolution "
            "side (SKU or variant-ID). Default `False` returns only live "
            "rows; on a duplicate SKU, the live row always wins. Set "
            "`True` only when inspecting a deleted variant directly."
        ),
    )


class LocationStock(BaseModel):
    """Per-location stock breakdown for a single variant.

    Threshold fields (``reorder_point``, ``safety_stock_level``) come from
    the per-(variant, location) inventory point — Katana stores reorder
    thresholds per warehouse, not globally. ``value_in_stock`` and
    ``average_cost`` round out the per-location picture so callers can see
    capital exposure per warehouse.
    """

    location_id: int
    location_name: str | None = None
    in_stock: float
    committed: float
    expected: float
    available: float
    reorder_point: float | None = None
    safety_stock_level: float | None = None
    value_in_stock: float | None = None
    average_cost: float | None = None
    # Per-row archive state — Katana lets an inventory row at a single
    # warehouse be archived independent of the variant's parent. Derived
    # from ``Inventory.archived_at`` (non-null = archived). Surfaces only
    # when the request opted in via ``include_archived=True`` (#539).
    is_archived: bool = False


class StockInfo(BaseModel):
    """Stock information for a variant. Totals are sums across locations
    (or a single location when ``location_id`` was supplied on the
    request); ``by_location`` carries the per-warehouse breakdown so
    callers can see where stock actually is without a follow-up query.

    Parent-derived context (``uom``, ``default_supplier_*``,
    ``parent_type``, ``katana_url``) is folded in from the parent
    product/material via the typed cache so the agent doesn't need a
    separate ``get_item`` call to know what unit they're looking at or
    where to place a follow-up PO.
    """

    variant_id: int | None = None
    sku: str
    product_name: str
    available_stock: float
    committed: float
    expected: float
    in_stock: float
    by_location: list[LocationStock] = Field(default_factory=list)
    # ``False`` for not-found stubs — ``_check_inventory_impl`` echoes
    # the input back in ``sku`` / ``variant_id`` so the JSON envelope
    # still names the row, but actionable UI affordances (Create PO,
    # View Variant Details) must be gated on this flag rather than
    # presence of ``sku`` / ``variant_id`` alone.
    is_found: bool = True

    # Parent-derived context (lifted from parent product/material via cache)
    uom: str | None = None
    default_supplier_id: int | None = None
    default_supplier_name: str | None = None
    parent_type: Literal["product", "material"] | None = None
    katana_url: str | None = None  # deep-link to parent page
    # Variant-level archive state lifted from ``CachedVariant.parent_archived_at``
    # — true when the parent product/material is archived. Mirrors the
    # ``ItemInfo.is_archived`` / ``ItemDetailsResponse.is_archived``
    # convention from #526 so callers don't have to inspect the timestamp.
    is_archived: bool = False


class _InventoryRow(NamedTuple):
    """Per-location inventory-point fields, parsed from the API response.

    Intermediate shape between the wire envelope and ``LocationStock`` —
    keeps the row-extraction loop terse and makes the comprehension that
    builds ``by_location`` readable without an 8-tuple positional unpack.
    """

    location_id: int
    in_stock: float
    committed: float
    expected: float
    reorder_point: float | None
    safety_stock_level: float | None
    value_in_stock: float | None
    average_cost: float | None
    is_archived: bool


async def _fetch_stock_for_variant(
    services: Any,
    variant_id: int,
    sku: str,
    product_name: str,
    location_id: int | None = None,
    *,
    include_archived: bool = False,
) -> StockInfo:
    """Query the inventory endpoint and return totals + per-location breakdown.

    When ``location_id`` is supplied, the API call is scoped to that
    location (so totals and ``by_location`` only cover one warehouse).
    Without the filter, totals are the sum across every location the
    variant has stock at, and ``by_location`` is sorted by ``in_stock``
    descending so the largest holding shows first.

    ``include_archived`` threads through to ``get_all_inventory_point`` so
    archived per-location inventory rows surface only on explicit opt-in
    (#539). The default keeps the active-only contract used by reorder
    planning callers.
    """
    from katana_public_api_client.api.inventory import get_all_inventory_point
    from katana_public_api_client.domain.converters import unwrap_unset
    from katana_public_api_client.utils import unwrap_data

    api_kwargs: dict[str, Any] = {"client": services.client, "variant_id": variant_id}
    if location_id is not None:
        api_kwargs["location_id"] = location_id
    if include_archived:
        api_kwargs["include_archived"] = True
    response = await get_all_inventory_point.asyncio_detailed(**api_kwargs)
    inventory_items = unwrap_data(response)

    # First pass: extract numbers + collect unique location IDs. Threshold
    # and value fields live on the inventory point per-location too — pull
    # them through so the card can render reorder-point bands and capital
    # exposure without a follow-up call.
    rows: list[_InventoryRow] = []
    total_in_stock = 0.0
    total_committed = 0.0
    total_expected = 0.0
    for inv in inventory_items:
        loc_id = unwrap_unset(inv.location_id, None)
        if loc_id is None:
            continue
        in_stock = float(unwrap_unset(inv.quantity_in_stock, "0"))
        committed = float(unwrap_unset(inv.quantity_committed, "0"))
        expected = float(unwrap_unset(inv.quantity_expected, "0"))
        total_in_stock += in_stock
        total_committed += committed
        total_expected += expected
        rows.append(
            _InventoryRow(
                location_id=loc_id,
                in_stock=in_stock,
                committed=committed,
                expected=expected,
                reorder_point=_opt_float(unwrap_unset(inv.reorder_point, None)),
                safety_stock_level=_opt_float(
                    unwrap_unset(inv.safety_stock_level, None)
                ),
                value_in_stock=_opt_float(unwrap_unset(inv.value_in_stock, None)),
                average_cost=_opt_float(unwrap_unset(inv.average_cost, None)),
                is_archived=unwrap_unset(inv.archived_at, None) is not None,
            )
        )

    # Batch the location-name lookups via the cache's bulk helper —
    # one query for N IDs instead of N round trips. Cache misses are
    # non-fatal (location_id alone is still useful to the caller).
    loc_names: dict[int, str | None] = {}
    if rows:
        unique_loc_ids = {row.location_id for row in rows}
        loc_lookups = await services.typed_cache.catalog.get_many_by_ids(
            CachedLocation, unique_loc_ids
        )
        loc_names = {lid: _attr(loc_lookups.get(lid), "name") for lid in unique_loc_ids}

    by_location = [
        LocationStock(
            location_id=row.location_id,
            location_name=loc_names.get(row.location_id),
            in_stock=row.in_stock,
            committed=row.committed,
            expected=row.expected,
            available=row.in_stock - row.committed,
            reorder_point=row.reorder_point,
            safety_stock_level=row.safety_stock_level,
            value_in_stock=row.value_in_stock,
            average_cost=row.average_cost,
            is_archived=row.is_archived,
        )
        for row in rows
    ]
    by_location.sort(key=lambda ls: ls.in_stock, reverse=True)
    return StockInfo(
        variant_id=variant_id,
        sku=sku,
        product_name=product_name,
        available_stock=total_in_stock - total_committed,
        committed=total_committed,
        expected=total_expected,
        in_stock=total_in_stock,
        by_location=by_location,
    )


async def _enrich_stock_info_with_parent(
    services: Any,
    results: list[StockInfo],
    *,
    variants_by_id: dict[int, Any] | None = None,
) -> None:
    """Mutate each :class:`StockInfo` in place with parent-derived context.

    ``variants_by_id`` carries the variants the caller already resolved
    (cache hit or API fallback). When provided, enrichment uses those
    rows directly — critical for the cold-cache variant-id path, where
    re-resolving from the cache alone would silently drop the
    just-fetched API row and lose UoM, supplier, parent type, and
    katana_url on the response.

    When the map is omitted, falls back to a bulk cache lookup with the
    archived/deleted flags so direct lookups in ``_check_inventory_impl``
    don't lose enrichment for soft-deleted rows.

    Bulk-loads parent products / materials / default suppliers via
    :func:`_enrich_variants_with_parent`. Variants without a
    ``variant_id`` (not-found stubs) are skipped silently. Cache misses
    on parent / supplier degrade gracefully — fields stay ``None`` and
    the card omits the corresponding lines.
    """
    from katana_mcp.tools.foundation.items import _enrich_variants_with_parent

    enrichable = [r for r in results if r.variant_id is not None]
    if not enrichable:
        return

    if variants_by_id is not None:
        variants: dict[int, Any] = variants_by_id
    else:
        variant_ids = [r.variant_id for r in enrichable if r.variant_id is not None]
        variants = await services.typed_cache.catalog.get_many_by_ids(
            CachedVariant,
            variant_ids,
            include_archived=True,
            include_deleted=True,
        )
    cache_variants = [v for v in variants.values() if v is not None]

    (
        products_by_id,
        materials_by_id,
        supplier_by_id,
    ) = await _enrich_variants_with_parent(services, cache_variants)

    parent_lookup: dict[Literal["product", "material"], dict[int, Any]] = {
        "product": products_by_id,
        "material": materials_by_id,
    }
    for r in enrichable:
        if r.variant_id is None:
            continue
        variant = variants.get(r.variant_id)
        # ``parent_archived_at`` is lifted onto the variant during sync;
        # surface it on the response as ``is_archived`` so callers don't
        # have to inspect the timestamp (mirrors #526's items-side
        # convention).
        r.is_archived = _attr(variant, "parent_archived_at") is not None
        # Variants carry exactly one of product_id / material_id; pick whichever
        # is set so the right parent map and URL kind get used.
        kind: Literal["product", "material"] | None
        if pid := _attr(variant, "product_id"):
            kind, parent_id = "product", pid
        elif mid := _attr(variant, "material_id"):
            kind, parent_id = "material", mid
        else:
            continue
        r.parent_type = kind
        r.katana_url = katana_web_url(kind, parent_id)
        parent = parent_lookup[kind].get(parent_id)
        if parent is None:
            continue
        r.uom = _attr(parent, "uom")
        sup_id = _attr(parent, "default_supplier_id")
        if sup_id:
            r.default_supplier_id = sup_id
            supplier = supplier_by_id.get(sup_id)
            r.default_supplier_name = _attr(supplier, "name")


def _opt_float(value: Any) -> float | None:
    """Coerce a string / number / None to ``float`` or ``None``.

    Optional inventory-point thresholds must surface as ``None`` when
    unset, never ``0.0`` — a coerced zero would silently flip the
    "below reorder point" check on every threshold-less row.
    """
    if value is None or value == "":
        return None
    return float(value)


async def _check_inventory_impl(
    request: CheckInventoryRequest, context: Context
) -> list[StockInfo]:
    """Look up one or more variants by SKU/ID and return their stock info.

    Output order matches input order — mixed `["SKU-1", 42, "SKU-2"]` returns
    results in that exact sequence.
    """
    # Normalize SKU inputs once; reject blank strings up front.
    items: list[str | int] = []
    for raw in request.skus_or_variant_ids:
        if isinstance(raw, str):
            normalized = raw.strip()
            if not normalized:
                raise ValueError("SKU cannot be empty")
            items.append(normalized)
        else:
            items.append(raw)

    sku_count = sum(1 for item in items if isinstance(item, str))
    start_time = time.monotonic()
    logger.info(
        "inventory_check_started",
        sku_count=sku_count,
        variant_id_count=len(items) - sku_count,
    )

    try:
        services = get_services(context)

        # ``_fetch_variant_by_id`` falls back to the API on cache miss so a
        # cold cache doesn't silently return empty stock.
        from katana_mcp.tools.foundation.items import _fetch_variant_by_id

        async def _fetch(item: str | int) -> tuple[StockInfo, Any | None]:
            """Returns ``(StockInfo, variant_or_None)`` so the variant we
            already resolved (cache hit or API fallback) can be reused
            during enrichment without a redundant lookup that would also
            silently drop API-fallback rows on a cold cache."""
            if isinstance(item, str):
                # Soft-state defaults are off (#539): on a duplicate SKU
                # the live row always wins via the ``get_by_sku``
                # tiebreaker. Cleanup workflows opt in via the request
                # flags so an archived-only or deleted-only SKU can still
                # be resolved.
                variant = await services.typed_cache.catalog.get_by_sku(
                    item,
                    include_archived=request.include_archived,
                    include_deleted=request.include_deleted,
                )
                if not variant:
                    logger.warning("inventory_check_not_found", sku=item)
                    return (
                        StockInfo(
                            sku=item,
                            product_name="",
                            available_stock=0,
                            committed=0,
                            expected=0,
                            in_stock=0,
                            is_found=False,
                        ),
                        None,
                    )
                stock = await _fetch_stock_for_variant(
                    services,
                    _attr(variant, "id"),
                    item,
                    _attr(variant, "display_name") or _attr(variant, "sku") or "",
                    location_id=request.location_id,
                    include_archived=request.include_archived,
                )
                return stock, variant

            variant = await _fetch_variant_by_id(
                services,
                item,
                include_archived=request.include_archived,
                include_deleted=request.include_deleted,
            )
            if not variant:
                logger.warning("inventory_check_not_found", variant_id=item)
                return (
                    StockInfo(
                        variant_id=item,
                        sku="",
                        product_name="",
                        available_stock=0,
                        committed=0,
                        expected=0,
                        in_stock=0,
                        is_found=False,
                    ),
                    None,
                )
            sku = _attr(variant, "sku") or ""
            # ``VariantResponse`` (API fallback) has no ``display_name`` and
            # SKU can be null; fall back to the nested parent's name (set by
            # ``extend=[PRODUCT_OR_MATERIAL]``) so the card title surfaces
            # the product/material name instead of degrading to "Unknown".
            parent = _attr(variant, "product_or_material")
            product_name = (
                _attr(variant, "display_name") or sku or _attr(parent, "name") or ""
            )
            stock = await _fetch_stock_for_variant(
                services,
                item,
                sku,
                product_name,
                location_id=request.location_id,
                include_archived=request.include_archived,
            )
            return stock, variant

        pairs = await asyncio.gather(*(_fetch(item) for item in items))
        results = [stock for stock, _ in pairs]
        # Reuse the variants we just resolved (whether from cache or via
        # the API-fallback path) so enrichment never goes back to a
        # cache-only lookup that would silently drop cold-cache rows.
        variants_by_id: dict[int, Any] = {
            stock.variant_id: variant
            for stock, variant in pairs
            if variant is not None and stock.variant_id is not None
        }

        # Fold parent-derived context (UoM, default supplier, parent type,
        # katana_url) into each result so the card surfaces decision-critical
        # facts without forcing the agent to chain a ``get_item`` call.
        await _enrich_stock_info_with_parent(
            services, results, variants_by_id=variants_by_id
        )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "inventory_check_completed",
            count=len(results),
            duration_ms=duration_ms,
        )
        return results

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "inventory_check_failed",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


@observe_tool
@unpack_pydantic_params
async def check_inventory(
    request: Annotated[CheckInventoryRequest, Unpack()], context: Context
) -> ToolResult:
    """Check current stock levels for one or more SKUs or variant IDs.

    Pass a list of SKUs (strings) or variant IDs (integers) — or mix both — to
    ``skus_or_variant_ids``. Returns the JSON ``{items: [...]}`` envelope for
    every request shape — single OR batch — so programmatic consumers see one
    stable contract. ``structured_content`` carries a rich Prefab card on
    every shape: the single-item card on a 1-item request, the batch summary
    + per-variant by-location card on N-item requests. Batching N checks in
    one call is faster than N separate invocations.

    By default returns totals summed across every location the variant has
    stock at, plus a per-location ``by_location`` breakdown so callers can
    see where stock actually is without a follow-up query. Pass
    ``location_id`` to filter to a single warehouse — totals and
    ``by_location`` then only cover that one location. Look up location
    IDs via the ``list_locations`` tool.

    Use before creating orders to verify stock availability, or with a
    batch list to check multiple ingredients at once (e.g. all EXPECTED
    items in an MO recipe).
    """
    from katana_mcp.tools.prefab_ui import (
        build_inventory_check_batch_ui,
        build_inventory_check_ui,
    )

    results = await _check_inventory_impl(request, context)

    # JSON content always uses the ``{items: [...]}`` envelope — single
    # OR batch — so programmatic consumers see one stable contract.
    # Pre-#567 the format="json" branch already returned this envelope;
    # the single-item bare-StockInfo content was markdown-only.
    payload = {"items": [r.model_dump(mode="json") for r in results]}
    content = json.dumps(payload, indent=2, default=str)

    # Batch path uses its own builder (#562).
    is_single = len(results) == 1 and len(request.skus_or_variant_ids) == 1
    if is_single:
        ui = build_inventory_check_ui(results[0].model_dump())
    else:
        ui = build_inventory_check_batch_ui([r.model_dump() for r in results])
    return ToolResult(content=content, structured_content=ui)


# ============================================================================
# Tool 2: list_low_stock_items
# ============================================================================


class LowStockRequest(BaseModel):
    """Request model for listing low stock items."""

    model_config = ConfigDict(extra="forbid")

    threshold: int = Field(default=10, description="Stock threshold level")
    limit: int = Field(default=50, description="Maximum items to return")
    include_archived: bool = Field(
        default=False,
        description=(
            "Include archived rows across both surfaces: per-location "
            "inventory records marked archived (threaded to `/inventory`, "
            "counted into `current_stock` and reported via "
            "`has_archived_inventory`) AND variants whose parent "
            "product/material is archived (reported via `is_archived`). "
            "Default `False` — archived rows shouldn't carry phantom "
            "stock signals into normal reorder planning. Set `True` "
            "for cleanup workflows."
        ),
    )


class LowStockItem(BaseModel):
    """Low stock item information.

    ``lead_time_days`` and ``minimum_order_quantity`` come from
    ``CachedVariant`` so the field is uniform across product- and
    material-parented variants — only products carry a parent-level
    ``lead_time``, so reading from the variant keeps both shapes
    symmetric.
    """

    sku: str
    product_name: str
    current_stock: float
    threshold: int
    display_name: str | None = None
    variant_id: int
    uom: str | None = None
    lead_time_days: int | None = None
    default_supplier_id: int | None = None
    default_supplier_name: str | None = None
    minimum_order_quantity: float | None = None
    # Variant-level archive state lifted from ``CachedVariant.parent_archived_at``
    # — true when the parent product/material is archived. Surfaces only
    # when the request opted in via ``include_archived=True`` (#539).
    is_archived: bool = False
    # Per-row inventory archive state — true when at least one of the
    # ``/inventory`` rows contributing to ``current_stock`` for this
    # variant is itself archived (``Inventory.archived_at`` non-null).
    # Distinct from ``is_archived`` (parent-archived); a variant with a
    # live parent can still have archived inventory rows at individual
    # warehouses. Only meaningful when the request opted in via
    # ``include_archived=True`` — otherwise archived rows never enter
    # the aggregation and the flag stays ``False``.
    has_archived_inventory: bool = False


class LowStockResponse(BaseModel):
    """Response containing low stock items."""

    items: list[LowStockItem]
    total_count: int


@cache_read(CachedVariant, CachedProduct, CachedMaterial, CachedSupplier)
async def _list_low_stock_items_impl(
    request: LowStockRequest, context: Context
) -> LowStockResponse:
    """Implementation of list_low_stock_items tool.

    Fetches every variant/location row from ``/inventory``, sums
    ``quantity_in_stock`` per variant across locations, filters to the
    variants below ``request.threshold``, then resolves SKU and product
    name from the cached variant index (with API fallback on cache miss).

    Args:
        request: Request with threshold and limit
        context: Server context with KatanaClient

    Returns:
        Low-stock items sorted ascending by current stock.

    Raises:
        ValueError: If threshold or limit are invalid
        Exception: If API call fails
    """
    if request.threshold < 0:
        raise ValueError("Threshold must be non-negative")
    if request.limit <= 0:
        raise ValueError("Limit must be positive")

    start_time = time.monotonic()
    logger.info(
        "low_stock_search_started",
        threshold=request.threshold,
        limit=request.limit,
    )

    try:
        from katana_mcp.tools.foundation.items import (
            _enrich_variants_with_parent,
            _fetch_variant_by_id,
        )
        from katana_public_api_client.api.inventory import get_all_inventory_point
        from katana_public_api_client.utils import unwrap_data

        services = get_services(context)

        # ``include_archived`` threads through so reorder planning stays
        # active-only by default (#539). Cleanup workflows pass
        # ``include_archived=True`` to surface archived rows.
        inventory_api_kwargs: dict[str, Any] = {"client": services.client}
        if request.include_archived:
            inventory_api_kwargs["include_archived"] = True
        response = await get_all_inventory_point.asyncio_detailed(
            **inventory_api_kwargs
        )
        inventory_rows = unwrap_data(response)

        totals: dict[int, float] = {}
        has_archived_rows: dict[int, bool] = {}
        for inv in inventory_rows:
            qty = float(unwrap_unset(inv.quantity_in_stock, "0"))
            totals[inv.variant_id] = totals.get(inv.variant_id, 0.0) + qty
            if unwrap_unset(inv.archived_at, None) is not None:
                has_archived_rows[inv.variant_id] = True

        low_stock = sorted(
            (
                (variant_id, total)
                for variant_id, total in totals.items()
                if total < request.threshold
            ),
            key=lambda pair: pair[1],
        )

        limited = low_stock[: request.limit]
        variant_ids = [variant_id for variant_id, _ in limited]

        catalog = services.typed_cache.catalog
        # ``include_archived=True`` matches ``ensure_variants_synced``'s
        # ingest semantics — archived variants live in the cache, so
        # bulk-reading without the flag would force the per-ID fallback
        # for every archived row in the low-stock set.
        cached_variants: dict[int, Any] = await catalog.get_many_by_ids(
            CachedVariant,
            variant_ids,
            include_archived=True,
            include_deleted=True,
        )

        # Resolve cache misses in parallel via the per-variant API
        # fallback so the parent collection is complete even on a cold
        # cache. Sequential awaits would serialize N HTTP round-trips.
        missing_ids = [vid for vid in variant_ids if cached_variants.get(vid) is None]
        if missing_ids:
            fetched = await asyncio.gather(
                *(_fetch_variant_by_id(services, vid) for vid in missing_ids)
            )
            for vid, v in zip(missing_ids, fetched, strict=True):
                cached_variants[vid] = v

        # Enrich parents + suppliers via the shared helper so the
        # product/material ID-collision split and the cold-cache
        # nested-parent graft stay in lockstep with the items.py path.
        (
            products_by_id,
            materials_by_id,
            supplier_by_id,
        ) = await _enrich_variants_with_parent(
            services, [v for v in cached_variants.values() if v is not None]
        )

        def _parent_for(v: Any) -> Any | None:
            if (pid := _attr(v, "product_id")) is not None:
                return products_by_id.get(pid)
            if (mid := _attr(v, "material_id")) is not None:
                return materials_by_id.get(mid)
            return None

        items: list[LowStockItem] = []
        for variant_id, total in limited:
            variant = cached_variants.get(variant_id)
            display_name = (
                _attr(variant, "display_name") or _attr(variant, "name") or ""
            )
            parent = _parent_for(variant)
            default_supplier_id = _attr(parent, "default_supplier_id")
            supplier = (
                supplier_by_id.get(default_supplier_id)
                if default_supplier_id is not None
                else None
            )
            items.append(
                LowStockItem(
                    sku=_attr(variant, "sku") or "",
                    product_name=display_name,
                    current_stock=total,
                    threshold=request.threshold,
                    display_name=display_name or None,
                    variant_id=variant_id,
                    uom=_attr(parent, "uom"),
                    lead_time_days=_attr(variant, "lead_time"),
                    default_supplier_id=default_supplier_id,
                    default_supplier_name=_attr(supplier, "name"),
                    minimum_order_quantity=_attr(variant, "minimum_order_quantity"),
                    is_archived=_attr(variant, "parent_archived_at") is not None,
                    has_archived_inventory=has_archived_rows.get(variant_id, False),
                )
            )

        result = LowStockResponse(items=items, total_count=len(low_stock))

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "low_stock_search_completed",
            threshold=request.threshold,
            total_count=result.total_count,
            returned_count=len(result.items),
            duration_ms=duration_ms,
        )
        return result

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "low_stock_search_failed",
            threshold=request.threshold,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


@observe_tool
@unpack_pydantic_params
async def list_low_stock_items(
    request: Annotated[LowStockRequest, Unpack()], context: Context
) -> ToolResult:
    """List items with stock levels below a threshold — useful for reorder planning.

    Returns items that need replenishment. Follow up with get_variant_details to find
    supplier info, then create_purchase_order to reorder.

    Default threshold is 10 units, default limit is 50 items.
    """
    from katana_mcp.tools.prefab_ui import build_low_stock_ui

    response = await _list_low_stock_items_impl(request, context)

    items_dicts = [item.model_dump() for item in response.items]
    ui = build_low_stock_ui(items_dicts, request.threshold, response.total_count)

    return make_tool_result(response, ui=ui)


# ============================================================================
# Tool 3: get_inventory_movements
# ============================================================================


class GetInventoryMovementsRequest(BaseModel):
    """Request model for querying inventory movements."""

    model_config = ConfigDict(extra="forbid")

    sku: str = Field(..., description="SKU to get movements for")
    limit: int = Field(default=50, description="Maximum movements to return")
    location_id: int | None = Field(
        default=None,
        description=(
            "Filter movements to a single warehouse/facility. "
            "Look up via `list_locations`."
        ),
    )
    resource_type: GetAllInventoryMovementsResourceType | None = Field(
        default=None,
        description=(
            "Filter movements by what caused them. Accepts one of: "
            "`SalesOrderRow`, `ManufacturingOrder`, "
            "`ManufacturingOrderRecipeRow`, `ProductionIngredient`, "
            "`PurchaseOrderRow`, `PurchaseOrderRecipeRow`, "
            "`StockAdjustmentRow`, `StockTransferRow`, `SystemGenerated`."
        ),
    )
    created_at_min: str | None = Field(
        default=None,
        description=(
            "ISO-8601 lower bound on `created_at` — when the movement "
            "record was first written. Useful as an audit-trail filter."
        ),
    )
    created_at_max: str | None = Field(
        default=None,
        description="ISO-8601 upper bound on `created_at`.",
    )
    updated_at_min: str | None = Field(
        default=None,
        description=(
            "ISO-8601 lower bound on `updated_at` — when the movement "
            "record was last modified. Useful for incremental sync."
        ),
    )
    updated_at_max: str | None = Field(
        default=None,
        description="ISO-8601 upper bound on `updated_at`.",
    )
    include_archived: bool = Field(
        default=False,
        description=(
            "Include movements for variants whose parent product/material "
            "is archived. Default `False` returns only active rows; on a "
            "duplicate SKU, the live row always wins. Set `True` for "
            "cleanup workflows."
        ),
    )
    include_deleted: bool = Field(
        default=False,
        description=(
            "Include movements for soft-deleted variants. Default `False` "
            "returns only live rows; on a duplicate SKU, the live row "
            "always wins. Set `True` only when inspecting a deleted "
            "variant directly."
        ),
    )


class MovementInfo(BaseModel):
    """A single inventory movement record.

    Exhaustive — every field Katana's ``InventoryMovement`` attrs model exposes
    is surfaced here (identity, location, resource pointers, valuation fields,
    timestamps, and rank) so callers don't need a follow-up lookup for standard
    fields. Field names match the canonical Pydantic/Katana names verbatim so
    LLM consumers can't confuse a rendered column header with a different
    field.
    """

    id: int
    variant_id: int
    location_id: int
    resource_type: str
    resource_id: int | None = None
    caused_by_order_no: str | None = None
    caused_by_resource_id: int | None = None
    movement_date: str
    quantity_change: float
    balance_after: float
    value_per_unit: float
    value_in_stock_after: float
    average_cost_after: float
    rank: int | None = None
    # created_at / updated_at are required on the generated InventoryMovement
    # attrs model. Typing them optional would mask real API/unwrap issues and
    # weaken the "exhaustive" contract we're pinning.
    created_at: str
    updated_at: str


class InventoryMovementsResponse(BaseModel):
    """Response containing inventory movements."""

    sku: str
    product_name: str
    movements: list[MovementInfo]
    total_count: int


_INVENTORY_MOVEMENTS_DATE_FIELDS = (
    "created_at_min",
    "created_at_max",
    "updated_at_min",
    "updated_at_max",
)


async def _get_inventory_movements_impl(
    request: GetInventoryMovementsRequest, context: Context
) -> InventoryMovementsResponse:
    """Look up variant by SKU via cache, then query inventory movements."""
    from katana_public_api_client.api.inventory_movements import (
        get_all_inventory_movements,
    )
    from katana_public_api_client.domain.converters import unwrap_unset
    from katana_public_api_client.utils import unwrap_data

    if not request.sku or not request.sku.strip():
        raise ValueError("SKU cannot be empty")
    if request.limit <= 0:
        raise ValueError("Limit must be positive")

    parsed_dates = parse_request_dates(request, _INVENTORY_MOVEMENTS_DATE_FIELDS)

    start_time = time.monotonic()
    logger.info("inventory_movements_started", sku=request.sku)

    try:
        services = get_services(context)

        # Soft-state defaults are off (#539): on a duplicate SKU the live
        # row always wins via the ``get_by_sku`` tiebreaker. Cleanup
        # workflows opt in via the request flags so movements for an
        # archived-only or deleted-only SKU can still be inspected.
        variant = await services.typed_cache.catalog.get_by_sku(
            request.sku,
            include_archived=request.include_archived,
            include_deleted=request.include_deleted,
        )
        if variant is None:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)
            logger.warning(
                "inventory_movements_not_found",
                sku=request.sku,
                duration_ms=duration_ms,
            )
            return InventoryMovementsResponse(
                sku=request.sku,
                product_name="",
                movements=[],
                total_count=0,
            )

        variant_id = _attr(variant, "id")
        product_name = _attr(variant, "display_name") or _attr(variant, "sku") or ""

        # Query inventory movements filtered by variant_id.
        #
        # IMPORTANT: ``request.limit`` is the user-facing row cap, NOT just a
        # per-page hint. The pagination transport treats the API ``limit``
        # query param as page size and walks every page up to ``max_pages``
        # unless ``extensions={"max_items": N}`` is set — without that
        # extension, ``limit=5`` would still return the full movement history
        # (issue #771). We bypass ``asyncio_detailed`` and call the generated
        # ``_get_kwargs`` / ``_build_response`` helpers directly so we can
        # pass ``extensions`` into the underlying httpx request and cap the
        # merged result at ``request.limit`` rows.
        #
        # Decouple page-size from row-cap: the per-page ``limit`` query param
        # must be clamped to Katana's documented max of 250 (see
        # ``docs/katana-openapi.yaml`` lines 21-24 — "Max page size: 250
        # records per request"). Otherwise ``request.limit=500`` would be sent
        # as ``?limit=500`` and Katana rejects it. The transport paginates
        # additional pages as needed up to ``max_items``.
        per_page_limit = min(request.limit, 250)
        kwargs = get_all_inventory_movements._get_kwargs(
            variant_ids=[variant_id],
            limit=per_page_limit,
            location_id=to_unset(request.location_id),
            resource_type=to_unset(request.resource_type),
            created_at_min=to_unset(parsed_dates["created_at_min"]),
            created_at_max=to_unset(parsed_dates["created_at_max"]),
            updated_at_min=to_unset(parsed_dates["updated_at_min"]),
            updated_at_max=to_unset(parsed_dates["updated_at_max"]),
        )
        kwargs["extensions"] = {"max_items": request.limit}
        httpx_response = await services.client.get_async_httpx_client().request(
            **kwargs
        )
        response = get_all_inventory_movements._build_response(
            client=services.client, response=httpx_response
        )
        attrs_list = unwrap_data(response)

        movements = [
            MovementInfo(
                id=m.id,
                variant_id=m.variant_id,
                location_id=m.location_id,
                resource_type=m.resource_type.value
                if hasattr(m.resource_type, "value")
                else str(m.resource_type),
                resource_id=unwrap_unset(m.resource_id, None),
                caused_by_order_no=unwrap_unset(m.caused_by_order_no, None),
                caused_by_resource_id=unwrap_unset(m.caused_by_resource_id, None),
                movement_date=_iso_str(m.movement_date),
                quantity_change=m.quantity_change,
                balance_after=m.balance_after,
                value_per_unit=m.value_per_unit,
                value_in_stock_after=m.value_in_stock_after,
                average_cost_after=m.average_cost_after,
                rank=unwrap_unset(m.rank, None),
                created_at=_iso_str(m.created_at),
                updated_at=_iso_str(m.updated_at),
            )
            for m in attrs_list
        ]

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "inventory_movements_completed",
            sku=request.sku,
            count=len(movements),
            duration_ms=duration_ms,
        )
        return InventoryMovementsResponse(
            sku=request.sku,
            product_name=product_name,
            movements=movements,
            total_count=len(movements),
        )

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "inventory_movements_failed",
            sku=request.sku,
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


@observe_tool
@unpack_pydantic_params
async def get_inventory_movements(
    request: Annotated[GetInventoryMovementsRequest, Unpack()], context: Context
) -> ToolResult:
    """Get inventory movement history for a SKU — every stock change with dates,
    quantities, valuation (value_per_unit, value_in_stock_after, average_cost_after),
    and what caused each movement (sales, purchases, manufacturing, adjustments).

    Single-SKU: pass the SKU of interest. For movements across multiple variants,
    call this tool once per variant (there is no batch shape for this tool).

    Exhaustive — every field Katana exposes on ``InventoryMovement`` is surfaced
    (identity, variant/location pointers, resource pointers, valuation fields,
    timestamps, rank) so callers don't need follow-up lookups for standard
    fields. Use to investigate stock discrepancies or trace how inventory levels
    changed over time. Default limit is 50 movements, ordered most recent first.

    Filter via optional ``location_id`` (single warehouse), ``resource_type``
    (one of ``SalesOrderRow``, ``ManufacturingOrder``,
    ``ManufacturingOrderRecipeRow``, ``ProductionIngredient``,
    ``PurchaseOrderRow``, ``PurchaseOrderRecipeRow``, ``StockAdjustmentRow``,
    ``StockTransferRow``, ``SystemGenerated``), and
    ``created_at_min``/``created_at_max``/``updated_at_min``/``updated_at_max``
    (ISO-8601 datetimes — audit-trail windows). For point-in-time inventory
    reconstruction, prefer ``inventory_at`` which walks movements and returns
    the balance ``as_of`` a specific moment.
    """
    response = await _get_inventory_movements_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Tool 4: inventory_at — point-in-time balance reconstruction
# ============================================================================


class InventoryAtRequest(BaseModel):
    """Request model for point-in-time inventory reconstruction."""

    model_config = ConfigDict(extra="forbid")

    skus_or_variant_ids: CoercedStrIntList = Field(
        ...,
        min_length=1,
        max_length=100,
        description=(
            "JSON array of SKUs (strings) or variant IDs (integers) — mix freely. "
            'E.g., ["WS74001", 12345] or ["WS74001", "WS74002"]. '
            "Output order matches input order. Max 100 items per call."
        ),
    )
    as_of: str = Field(
        ...,
        description=(
            "ISO-8601 datetime. Returns the balance as of this moment by "
            "walking inventory movements and picking the most recent "
            "movement at-or-before `as_of` per location."
        ),
    )
    location_id: int | None = Field(
        default=None,
        description=(
            "Filter to a single warehouse/facility. When set, only "
            "movements at this location are considered."
        ),
    )
    include_archived: bool = Field(
        default=False,
        description=(
            "Include variants whose parent product/material is archived. "
            "Default `False` returns only active rows; on a duplicate SKU, "
            "the live row always wins. Set `True` for cleanup workflows."
        ),
    )
    include_deleted: bool = Field(
        default=False,
        description=(
            "Include soft-deleted variants. Default `False` returns only "
            "live rows; on a duplicate SKU, the live row always wins. "
            "Set `True` only when inspecting a deleted variant directly."
        ),
    )


class InventoryAtLocation(BaseModel):
    """Per-location balance snapshot at `as_of`."""

    location_id: int
    location_name: str | None = None
    balance_at: float
    value_in_stock_at: float
    average_cost_at: float
    last_movement_date: str
    last_movement_id: int


class InventoryAtItem(BaseModel):
    """Per-variant point-in-time balance with location breakdown.

    `sku` may be ``None`` — Katana allows variants without SKUs
    (legacy NetSuite imports are a common source). See the documented
    invariant in CLAUDE.md.
    """

    variant_id: int
    sku: str | None
    display_name: str
    by_location: list[InventoryAtLocation] = Field(default_factory=list)
    total_balance: float = 0.0
    total_value: float = 0.0


class InventoryAtResponse(BaseModel):
    """Response containing point-in-time balances per variant."""

    as_of: str
    items: list[InventoryAtItem]
    not_found: list[str | int] = Field(default_factory=list)


_INVENTORY_AT_CHUNK_SIZE = 20  # variant_ids per movements-fetch call


async def _inventory_at_impl(
    request: InventoryAtRequest, context: Context
) -> InventoryAtResponse:
    """Reconstruct inventory balance at a specific point in time.

    The Katana ``/inventory`` endpoint is snapshot-only. To answer "what
    was the balance on date X", walk ``/inventory_movements`` for each
    variant, filter to ``movement_date <= as_of``, then per location pick
    the most recent matching row and read its ``balance_after`` /
    ``value_in_stock_after`` / ``average_cost_after`` fields (the running
    totals Katana computes as each movement lands).

    Movements are fetched in chunks of variant_ids — the auto-paginating
    transport collects multiple pages, capped at 25k movements per call,
    so a chunk size of 20 keeps headroom for variants with high movement
    velocity.
    """
    from katana_mcp.tools.foundation.items import _fetch_variant_by_id
    from katana_public_api_client.api.inventory_movements import (
        get_all_inventory_movements,
    )
    from katana_public_api_client.utils import unwrap_data

    parsed_as_of = parse_iso_datetime(request.as_of, "as_of")
    as_of_dt = naive_utc(parsed_as_of)
    assert as_of_dt is not None  # parse_iso_datetime always returns datetime

    items: list[str | int] = []
    for raw in request.skus_or_variant_ids:
        if isinstance(raw, str):
            normalized = raw.strip()
            if not normalized:
                raise ValueError("SKU cannot be empty")
            items.append(normalized)
        else:
            items.append(raw)

    start_time = time.monotonic()
    sku_count = sum(1 for item in items if isinstance(item, str))
    logger.info(
        "inventory_at_started",
        sku_count=sku_count,
        variant_id_count=len(items) - sku_count,
        as_of=request.as_of,
    )

    try:
        services = get_services(context)

        async def _resolve(item: str | int) -> tuple[str | int, Any | None]:
            if isinstance(item, str):
                v = await services.typed_cache.catalog.get_by_sku(
                    item,
                    include_archived=request.include_archived,
                    include_deleted=request.include_deleted,
                )
            else:
                v = await _fetch_variant_by_id(
                    services,
                    item,
                    include_archived=request.include_archived,
                    include_deleted=request.include_deleted,
                )
            return (item, v)

        resolved_pairs = list(await asyncio.gather(*(_resolve(i) for i in items)))

        not_found: list[str | int] = []
        # dict preserves first-seen input order; duplicate inputs collapse
        # to one entry naturally without a separate dedup set.
        input_to_variant: dict[str | int, tuple[int, str | None, str]] = {}
        for item, variant in resolved_pairs:
            if item in input_to_variant:
                continue
            vid = _attr(variant, "id") if variant is not None else None
            if vid is None:
                not_found.append(item)
                continue
            sku = _attr(variant, "sku")
            display_name = _attr(variant, "display_name") or sku or ""
            input_to_variant[item] = (vid, sku, display_name)

        # Chunk variant_ids so we don't blow through the 25k-movement
        # auto-pagination cap. 20 ids x ~1k movements/variant keeps headroom.
        # Chunks fetch concurrently — independent network I/O dominates.
        unique_vids = {vid for vid, _, _ in input_to_variant.values()}
        chunks = list(batched(sorted(unique_vids), _INVENTORY_AT_CHUNK_SIZE))

        async def _fetch_chunk(chunk: tuple[int, ...]) -> list[Any]:
            response = await get_all_inventory_movements.asyncio_detailed(
                client=services.client,
                variant_ids=list(chunk),
                location_id=to_unset(request.location_id),
            )
            return list(unwrap_data(response))

        chunk_results = await asyncio.gather(*(_fetch_chunk(c) for c in chunks))
        all_movements: list[Any] = [m for batch in chunk_results for m in batch]

        # Reduce: for each (variant_id, location_id), keep the movement
        # with max (movement_date, id) among those <= as_of_dt. The id
        # tie-break ensures deterministic output when multiple movements
        # share a back-dated timestamp.
        latest: dict[tuple[int, int], Any] = {}
        for m in all_movements:
            md = naive_utc(m.movement_date)
            if md is None or md > as_of_dt:
                continue
            key = (m.variant_id, m.location_id)
            existing = latest.get(key)
            if existing is None:
                latest[key] = m
                continue
            existing_md = naive_utc(existing.movement_date)
            if existing_md is None or (md, m.id) > (existing_md, existing.id):
                latest[key] = m

        unique_loc_ids = {loc_id for _, loc_id in latest}
        loc_names: dict[int, str | None] = {}
        if unique_loc_ids:
            loc_lookups = await services.typed_cache.catalog.get_many_by_ids(
                CachedLocation, unique_loc_ids
            )
            loc_names = {
                lid: _attr(loc_lookups.get(lid), "name") for lid in unique_loc_ids
            }

        result_items: list[InventoryAtItem] = []
        for _input, (vid, sku, display_name) in input_to_variant.items():
            by_loc_rows: list[InventoryAtLocation] = []
            total_balance = 0.0
            total_value = 0.0
            for (m_vid, loc_id), m in latest.items():
                if m_vid != vid:
                    continue
                balance = float(m.balance_after)
                value = float(m.value_in_stock_after)
                by_loc_rows.append(
                    InventoryAtLocation(
                        location_id=loc_id,
                        location_name=loc_names.get(loc_id),
                        balance_at=balance,
                        value_in_stock_at=value,
                        average_cost_at=float(m.average_cost_after),
                        last_movement_date=_iso_str(m.movement_date),
                        last_movement_id=m.id,
                    )
                )
                total_balance += balance
                total_value += value
            by_loc_rows.sort(key=lambda r: r.balance_at, reverse=True)
            result_items.append(
                InventoryAtItem(
                    variant_id=vid,
                    sku=sku,
                    display_name=display_name,
                    by_location=by_loc_rows,
                    total_balance=total_balance,
                    total_value=total_value,
                )
            )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "inventory_at_completed",
            items=len(result_items),
            not_found_count=len(not_found),
            duration_ms=duration_ms,
        )
        return InventoryAtResponse(
            as_of=request.as_of,
            items=result_items,
            not_found=not_found,
        )

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "inventory_at_failed",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


@observe_tool
@unpack_pydantic_params
async def inventory_at(
    request: Annotated[InventoryAtRequest, Unpack()], context: Context
) -> ToolResult:
    """Reconstruct inventory balance at a specific point in time by walking
    movement history.

    Pass a list of SKUs and/or variant IDs (mix freely), plus an ISO-8601
    ``as_of`` datetime, to get the on-hand quantity, total value, and rolling
    average cost as they stood at that moment — per location. Optionally
    filter to a single ``location_id``.

    Walks the variant's ``inventory_movements`` ledger, picks the most recent
    movement at-or-before ``as_of`` per location, and returns the snapshot
    fields (``balance_after`` / ``value_in_stock_after`` / ``average_cost_after``)
    that movement left behind. Variants with no movements before ``as_of``
    return an empty ``by_location`` list (no stock at that moment).

    Use for historical reconstruction and audit. For current state, use
    ``check_inventory`` — that's a single direct call against ``/inventory``
    and is faster when you only need "now". Use ``get_inventory_movements``
    to see the underlying delta stream.

    Returns a card UI plus the JSON envelope ``{as_of, items, not_found}``.
    Unresolved SKUs/IDs land in ``not_found``.
    """
    from katana_mcp.tools.prefab_ui import build_inventory_at_ui

    response = await _inventory_at_impl(request, context)

    items_dump = [item.model_dump(mode="json") for item in response.items]
    payload = {
        "as_of": response.as_of,
        "items": items_dump,
        "not_found": response.not_found,
    }
    content = json.dumps(payload, indent=2, default=str)

    ui = build_inventory_at_ui(
        items=items_dump,
        as_of=response.as_of,
        location_id=request.location_id,
        not_found=list(response.not_found),
    )
    return ToolResult(content=content, structured_content=ui)


# ============================================================================
# Tool 5: create_stock_adjustment
# ============================================================================


class StockAdjustmentBatchAllocation(BaseModel):
    """Allocate a portion of a row's adjustment quantity to a specific batch.

    Required for batch-tracked materials so adjustments land on the right
    batch record. The summed ``quantity`` across an item's batch_transactions
    should equal the row-level ``quantity`` being adjusted.
    """

    model_config = ConfigDict(extra="forbid")

    batch_id: int = Field(..., description="Batch ID to allocate adjustment to")
    quantity: float = Field(
        ..., description="Quantity allocated to this batch (signed like the row)"
    )


class StockAdjustmentRow(BaseModel):
    """A single line item in a stock adjustment."""

    model_config = ConfigDict(extra="forbid")

    sku: str = Field(..., description="SKU to adjust")
    quantity: float = Field(
        ..., description="Quantity change (positive to add, negative to remove)"
    )
    cost_per_unit: float | None = Field(
        default=None, description="Cost per unit (optional)"
    )
    batch_transactions: list[StockAdjustmentBatchAllocation] | None = Field(
        default=None,
        description=(
            "Per-batch allocation list. Required for batch-tracked materials — "
            "Katana rejects batch-tracked adjustments without it. Each entry: "
            "`{batch_id, quantity}`; summed quantity across batch_transactions "
            "should equal this row's quantity. Leave None for non-batch-tracked "
            "items."
        ),
    )


class CreateStockAdjustmentRequest(BaseModel):
    """Request to create a stock adjustment."""

    model_config = ConfigDict(extra="forbid")

    location_id: int = Field(
        ...,
        description=("Location ID for the adjustment. Look up via `list_locations`."),
    )
    rows: list[StockAdjustmentRow] = Field(..., description="Line items to adjust")
    reason: str | None = Field(
        default=None, description="Reason for adjustment (e.g., 'Sample received')"
    )
    additional_info: str | None = Field(default=None, description="Additional notes")
    stock_adjustment_number: str | None = Field(
        default=None,
        description=(
            "Adjustment number (optional). Leave None and the tool will generate "
            "a `SA-<timestamp>` default — Katana's API requires the field but "
            "doesn't auto-assign one. Supply only when importing from an external "
            "system or you need a specific number."
        ),
    )
    stock_adjustment_date: WireDatetime | None = Field(
        default=None,
        description=(
            "Date the adjustment occurred (ISO 8601). Leave None to stamp the "
            "current call time; supply for back-fills or to reflect the actual "
            "physical-count date when different from the call time."
        ),
    )
    preview: bool = Field(
        default=True,
        description="Set true (default) to preview, false to create",
    )
    include_archived: bool = Field(
        default=False,
        description=(
            "Include variants whose parent product/material is archived "
            "when resolving row SKUs. Default `False` errors on archived-"
            "only SKUs ('SKU not found'); set `True` for cleanup workflows "
            "that need to adjust stock on an archived item."
        ),
    )
    include_deleted: bool = Field(
        default=False,
        description=(
            "Include soft-deleted variants when resolving row SKUs. Default "
            "`False` errors on deleted-only SKUs; on a duplicate SKU, the "
            "live row always wins regardless. Set `True` only for "
            "exceptional cleanup workflows."
        ),
    )


class StockAdjustmentRowSummary(BaseModel):
    """One line item in a stock adjustment, in display-ready form.

    Carries enough data for the Prefab card's DataTable + the markdown
    fallback. ``display_name`` resolves the SKU to the variant's human-
    readable name at preview/apply time so the card doesn't have to
    re-fetch.
    """

    sku: str
    display_name: str
    quantity: float
    cost_per_unit: float | None = None


class StockAdjustmentResponse(BaseModel):
    """Response from stock adjustment creation."""

    id: int | None
    is_preview: bool
    location_id: int
    message: str
    rows: list[StockAdjustmentRowSummary] = Field(default_factory=list)
    rows_summary: str
    reason: str | None = None
    katana_url: str | None = None


async def _create_stock_adjustment_impl(
    request: CreateStockAdjustmentRequest, context: Context
) -> StockAdjustmentResponse:
    """Create a stock adjustment, resolving SKUs to variant IDs."""
    from datetime import UTC, datetime

    from katana_public_api_client.api.stock_adjustment import create_stock_adjustment
    from katana_public_api_client.client_types import UNSET
    from katana_public_api_client.domain.converters import to_unset
    from katana_public_api_client.models import (
        CreateStockAdjustmentRequest as APICreateStockAdjustmentRequest,
        StockAdjustmentBatchTransaction as APISABatchTransaction,
    )
    from katana_public_api_client.models.create_stock_adjustment_request_stock_adjustment_rows_item import (
        CreateStockAdjustmentRequestStockAdjustmentRowsItem,
    )

    if not request.rows:
        raise ValueError("At least one adjustment row is required")

    services = get_services(context)

    # Resolve SKUs to variant IDs
    api_rows = []
    rows_summary_parts = []
    structured_rows: list[StockAdjustmentRowSummary] = []
    for row in request.rows:
        # Soft-state defaults are off (#539): on a duplicate SKU the live
        # row always wins via the ``get_by_sku`` tiebreaker. A bare
        # ``create_stock_adjustment`` against an archived-only / deleted-
        # only SKU fails fast with "SKU not found" rather than letting
        # Katana reject downstream. Cleanup workflows opt in explicitly.
        variant = await services.typed_cache.catalog.get_by_sku(
            row.sku,
            include_archived=request.include_archived,
            include_deleted=request.include_deleted,
        )
        if variant is None:
            raise ValueError(f"SKU '{row.sku}' not found")
        display_name = _attr(variant, "display_name") or row.sku

        batch_txns: list[APISABatchTransaction] | Unset = UNSET
        if row.batch_transactions is not None:
            batch_txns = [
                APISABatchTransaction(quantity=bt.quantity, batch_id=bt.batch_id)
                for bt in row.batch_transactions
            ]

        api_rows.append(
            CreateStockAdjustmentRequestStockAdjustmentRowsItem(
                variant_id=_attr(variant, "id"),
                quantity=row.quantity,
                cost_per_unit=to_unset(row.cost_per_unit),
                batch_transactions=batch_txns,
            )
        )
        rows_summary_parts.append(f"- {row.sku} ({display_name}): {row.quantity:+.1f}")
        structured_rows.append(
            StockAdjustmentRowSummary(
                sku=row.sku,
                display_name=display_name,
                quantity=row.quantity,
                cost_per_unit=row.cost_per_unit,
            )
        )

    rows_summary = "\n".join(rows_summary_parts)

    # Preview mode
    if request.preview:
        return StockAdjustmentResponse(
            id=None,
            is_preview=True,
            location_id=request.location_id,
            message="Preview — call again with preview=false to create",
            rows=structured_rows,
            rows_summary=rows_summary,
            reason=request.reason,
        )

    # Caller-supplied stock_adjustment_number takes precedence; otherwise
    # generate a collision-resistant default. Katana's API requires the field
    # but doesn't auto-assign one.
    adj_number = (
        request.stock_adjustment_number
        if request.stock_adjustment_number is not None
        else f"SA-{datetime.now(tz=UTC).strftime('%Y%m%d-%H%M%S')}"
    )

    # stock_adjustment_date: caller-supplied wins; default to call time so the
    # field is always populated (Katana requires a value).
    adj_date = (
        request.stock_adjustment_date
        if request.stock_adjustment_date is not None
        else datetime.now(tz=UTC)
    )

    api_request = APICreateStockAdjustmentRequest(
        location_id=request.location_id,
        stock_adjustment_rows=api_rows,
        stock_adjustment_number=adj_number,
        stock_adjustment_date=adj_date,
        reason=to_unset(request.reason),
        additional_info=to_unset(request.additional_info),
    )

    response = await create_stock_adjustment.asyncio_detailed(
        client=services.client, body=api_request
    )

    # unwrap raises ValidationError (422), APIError, etc. with formatted messages
    from katana_public_api_client.utils import APIError, unwrap

    try:
        result = unwrap(response)
    except APIError as e:
        # Log the raw response for debugging
        logger.error(
            "stock_adjustment_api_error",
            status_code=response.status_code,
            raw_body=response.content.decode() if response.content else "",
            parsed=str(response.parsed),
        )
        raise ValueError(str(e)) from e

    adj_id = getattr(result, "id", None) if result else None
    return StockAdjustmentResponse(
        id=adj_id,
        is_preview=False,
        location_id=request.location_id,
        message="Stock adjustment created successfully",
        rows=structured_rows,
        rows_summary=rows_summary,
        reason=request.reason,
        katana_url=katana_web_url("stock_adjustment", adj_id),
    )


@observe_tool
@unpack_pydantic_params
async def create_stock_adjustment(
    request: Annotated[CreateStockAdjustmentRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a stock adjustment to correct inventory levels.

    Two-step flow: preview=true (default) to preview, preview=false to create
    (prompts for confirmation). Resolves SKUs to variant IDs automatically.

    Use positive quantities to add stock, negative to remove.
    """
    from katana_mcp.tools.prefab_ui import build_stock_adjustment_create_ui
    from katana_mcp.tools.tool_result_utils import make_tool_result

    response = await _create_stock_adjustment_impl(request, context)
    ui = build_stock_adjustment_create_ui(
        response.model_dump(),
        confirm_request=request,
        confirm_tool="create_stock_adjustment",
    )
    return make_tool_result(response, ui=ui)


# ============================================================================
# Tool 5: list_stock_adjustments
# ============================================================================


class ListStockAdjustmentsRequest(BaseModel):
    """Request to list/filter stock adjustments."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(
        default=50,
        ge=1,
        le=250,
        description=(
            "Max adjustments to return (default 50, min 1, max 250). When "
            "`page` is set, acts as the page size for that request."
        ),
    )
    page: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Page number (1-based). When set, the response includes "
            "pagination metadata describing total records and pages. "
            "Invalid pages (0, negative) are rejected at the schema boundary."
        ),
    )
    location_id: int | None = Field(
        default=None,
        description=("Filter by location ID. Look up via `list_locations`."),
    )
    ids: CoercedIntListOpt = Field(
        default=None,
        description=(
            "Restrict to a specific set of stock adjustment IDs. "
            "JSON array of integers, e.g. [101, 202, 303]."
        ),
    )
    stock_adjustment_number: str | None = Field(
        default=None, description="Exact match on the stock adjustment number"
    )
    created_after: str | None = Field(
        default=None,
        description="ISO-8601 datetime lower bound on created_at",
    )
    created_before: str | None = Field(
        default=None,
        description="ISO-8601 datetime upper bound on created_at",
    )
    updated_after: str | None = Field(
        default=None,
        description="ISO-8601 datetime lower bound on updated_at (useful for sync)",
    )
    updated_before: str | None = Field(
        default=None,
        description="ISO-8601 datetime upper bound on updated_at",
    )
    include_deleted: bool = Field(
        default=False,
        description="Include soft-deleted adjustments in the result",
    )

    variant_id: int | None = Field(
        default=None,
        description="Filter to adjustments that touch this variant ID",
    )
    reason: str | None = Field(
        default=None,
        description="Case-insensitive substring match on the `reason` field",
    )

    include_rows: bool = Field(
        default=False,
        description="When true, populate row-level detail on each summary",
    )


class StockAdjustmentRowInfo(BaseModel):
    """Summary of a stock adjustment line item."""

    id: int | None
    variant_id: int
    quantity: float
    cost_per_unit: float | None


class StockAdjustmentSummary(BaseModel):
    """Summary row for a stock adjustment in a list."""

    id: int
    stock_adjustment_number: str
    location_id: int
    stock_adjustment_date: str | None
    created_at: str | None
    updated_at: str | None
    reason: str | None
    additional_info: str | None
    row_count: int
    rows: list[StockAdjustmentRowInfo] | None = None
    katana_url: str | None = None


class ListStockAdjustmentsResponse(BaseModel):
    """Response containing a list of stock adjustments."""

    adjustments: list[StockAdjustmentSummary]
    total_count: int
    pagination: PaginationMeta | None = Field(
        default=None,
        description=(
            "Pagination metadata — populated when the caller requests a "
            "specific `page`; `None` otherwise."
        ),
    )


_STOCK_ADJUSTMENT_DATE_FIELDS = (
    "created_after",
    "created_before",
    "updated_after",
    "updated_before",
)


def _apply_stock_adjustment_filters(
    stmt: Any,
    request: ListStockAdjustmentsRequest,
    parsed_dates: dict[str, datetime | None],
) -> Any:
    """Translate request filters into WHERE clauses on a CachedStockAdjustment query.

    Shared by the data SELECT and the COUNT SELECT so pagination totals
    reflect exactly the same filter set as the data rows. ``parsed_dates``
    must come from :func:`parse_request_dates` — keeping parsing out of
    this function lets the paginated path avoid re-parsing on the COUNT
    query.
    """
    from sqlmodel import exists, select

    from katana_public_api_client.models_pydantic._generated import (
        CachedStockAdjustment,
        CachedStockAdjustmentRow,
    )

    if request.location_id is not None:
        stmt = stmt.where(CachedStockAdjustment.location_id == request.location_id)
    if request.ids is not None:
        stmt = stmt.where(CachedStockAdjustment.id.in_(request.ids))
    if request.stock_adjustment_number is not None:
        stmt = stmt.where(
            CachedStockAdjustment.stock_adjustment_number
            == request.stock_adjustment_number
        )
    if not request.include_deleted:
        stmt = stmt.where(CachedStockAdjustment.deleted_at.is_(None))

    # ``variant_id`` is a row-level field — EXISTS subquery scans the
    # indexed FK directly so a match on any row of any adjustment is
    # found regardless of pagination position.
    if request.variant_id is not None:
        row_filter = (
            select(CachedStockAdjustmentRow.id)
            .where(
                CachedStockAdjustmentRow.stock_adjustment_id
                == CachedStockAdjustment.id,
                CachedStockAdjustmentRow.variant_id == request.variant_id,
            )
            .correlate(CachedStockAdjustment)
        )
        stmt = stmt.where(exists(row_filter))

    if request.reason is not None:
        needle = request.reason.strip()
        if needle:
            stmt = stmt.where(CachedStockAdjustment.reason.ilike(f"%{needle}%"))

    return apply_date_window_filters(
        stmt,
        parsed_dates,
        ge_pairs={
            "created_after": CachedStockAdjustment.created_at,
            "updated_after": CachedStockAdjustment.updated_at,
        },
        le_pairs={
            "created_before": CachedStockAdjustment.created_at,
            "updated_before": CachedStockAdjustment.updated_at,
        },
    )


async def _list_stock_adjustments_impl(
    request: ListStockAdjustmentsRequest, context: Context
) -> ListStockAdjustmentsResponse:
    """List stock adjustments with filters via the typed cache.

    ``ensure_stock_adjustments_synced`` runs an incremental
    ``updated_at_min`` delta (debounced — see :data:`_SYNC_DEBOUNCE`).
    Filters translate to indexed SQL; ``variant_id`` runs as an EXISTS
    subquery against the row table so a match on any row is found
    regardless of how many adjustments precede it. See ADR-0018.
    """
    from sqlalchemy.orm import selectinload
    from sqlmodel import func, select

    from katana_mcp.typed_cache import ensure_stock_adjustments_synced
    from katana_public_api_client.models_pydantic._generated import (
        CachedStockAdjustment,
        CachedStockAdjustmentRow,
    )

    services = get_services(context)

    await ensure_stock_adjustments_synced(services.client, services.typed_cache)

    parsed_dates = parse_request_dates(request, _STOCK_ADJUSTMENT_DATE_FIELDS)

    # When ``include_rows`` is set, ``selectinload`` eager-loads the
    # children, so ``len(adj.stock_adjustment_rows)`` is free at
    # materialization time and we skip the correlated COUNT subquery.
    if request.include_rows:
        stmt = select(CachedStockAdjustment).options(
            selectinload(CachedStockAdjustment.stock_adjustment_rows)
        )
    else:
        row_count_subq = (
            select(func.count(CachedStockAdjustmentRow.id))
            .where(
                CachedStockAdjustmentRow.stock_adjustment_id == CachedStockAdjustment.id
            )
            .correlate(CachedStockAdjustment)
            .scalar_subquery()
            .label("row_count")
        )
        stmt = select(CachedStockAdjustment, row_count_subq)
    stmt = _apply_stock_adjustment_filters(stmt, request, parsed_dates)
    stmt = stmt.order_by(
        CachedStockAdjustment.created_at.desc(),
        CachedStockAdjustment.id.desc(),
    )
    if request.page is not None:
        stmt = stmt.offset((request.page - 1) * request.limit).limit(request.limit)
    else:
        stmt = stmt.limit(request.limit)

    async with services.typed_cache.session() as session:
        data_result = await session.exec(stmt)
        if request.include_rows:
            cached_adjustments = list(data_result.all())
            adjustments_with_counts: list[tuple[CachedStockAdjustment, int]] = [
                (adj, len(adj.stock_adjustment_rows)) for adj in cached_adjustments
            ]
        else:
            adjustments_with_counts = data_result.all()

        pagination: PaginationMeta | None = None
        if request.page is not None:
            count_stmt = _apply_stock_adjustment_filters(
                select(func.count()).select_from(CachedStockAdjustment),
                request,
                parsed_dates,
            )
            total_records = (await session.exec(count_stmt)).one()
            total_pages = (total_records + request.limit - 1) // request.limit
            pagination = PaginationMeta(
                total_records=total_records,
                total_pages=total_pages,
                page=request.page,
                first_page=request.page == 1,
                last_page=request.page >= total_pages,
            )

    adjustments: list[StockAdjustmentSummary] = []
    for adj, row_count in adjustments_with_counts:
        row_infos: list[StockAdjustmentRowInfo] | None = None
        if request.include_rows:
            row_infos = [
                StockAdjustmentRowInfo(
                    id=row.id,
                    variant_id=row.variant_id,
                    quantity=row.quantity,
                    cost_per_unit=row.cost_per_unit,
                )
                for row in adj.stock_adjustment_rows
            ]
        adjustments.append(
            StockAdjustmentSummary(
                id=adj.id,
                stock_adjustment_number=adj.stock_adjustment_number,
                location_id=adj.location_id,
                stock_adjustment_date=iso_or_none(adj.stock_adjustment_date),
                created_at=iso_or_none(adj.created_at),
                updated_at=iso_or_none(adj.updated_at),
                reason=adj.reason,
                additional_info=adj.additional_info,
                row_count=row_count,
                rows=row_infos,
                katana_url=katana_web_url("stock_adjustment", adj.id),
            )
        )

    return ListStockAdjustmentsResponse(
        adjustments=adjustments,
        total_count=len(adjustments),
        pagination=pagination,
    )


@observe_tool
@unpack_pydantic_params
async def list_stock_adjustments(
    request: Annotated[ListStockAdjustmentsRequest, Unpack()], context: Context
) -> ToolResult:
    """List stock adjustments with filters — pass `ids=[1,2,3]` to fetch a specific batch by ID (cache-backed).

    For batch lookup by known IDs, pass `ids=[...]` and get a summary table back in
    a single call. Use for discovery — find recent adjustments at a location,
    adjustments touching a specific variant, or adjustments matching a reason substring.
    Returns summary rows (number, location, dates, reason, row count). Set
    `include_rows=true` to also populate per-row details (variant_id, quantity,
    cost_per_unit).

    **Paging**
    - `limit` caps the number of rows returned (default 50, min 1).
    - Set `page=N` for explicit paging; the response includes `pagination`
      metadata (total_records, total_pages, first/last flags) computed from
      a SQL COUNT against the same filter predicate.
    - Otherwise the response returns up to `limit` rows ordered by created_at
      desc with no pagination metadata.

    **Filters** all run as indexed SQL against the typed cache:
    - `location_id`, `ids`, `stock_adjustment_number`, `include_deleted` —
      direct column filters.
    - `variant_id` — EXISTS subquery on the rows table (no page-bound
      truncation; an adjustment touching the variant is found regardless
      of how many other adjustments precede it).
    - `reason` — case-insensitive `ILIKE %needle%`.
    - `created_after`/`before`, `updated_after`/`before` — date-range
      bounds on the corresponding columns.
    """
    response = await _list_stock_adjustments_impl(request, context)
    return make_json_result(response)


# ============================================================================
# Tool 6: update_stock_adjustment
# ============================================================================


class UpdateStockAdjustmentParams(BaseModel):
    """Request to update an existing stock adjustment."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Stock adjustment ID to update")
    stock_adjustment_number: str | None = Field(
        default=None, description="New adjustment number (optional)"
    )
    stock_adjustment_date: WireDatetime | None = Field(
        default=None, description="New adjustment date (ISO-8601, optional)"
    )
    location_id: int | None = Field(
        default=None,
        description=("New location ID (optional). Look up via `list_locations`."),
    )
    reason: str | None = Field(default=None, description="New reason (optional)")
    additional_info: str | None = Field(
        default=None, description="New additional_info (optional)"
    )
    preview: bool = Field(
        default=True,
        description="If true (default), returns a preview. If false, applies the update.",
    )


class UpdateStockAdjustmentResponse(BaseModel):
    """Response from updating a stock adjustment."""

    id: int
    is_preview: bool
    stock_adjustment_number: str | None = None
    location_id: int | None = None
    stock_adjustment_date: str | None = None
    reason: str | None = None
    additional_info: str | None = None
    changes_summary: str
    message: str
    katana_url: str | None = None


def _format_changes_summary(request: UpdateStockAdjustmentParams) -> str:
    """Build a human-readable summary of the fields the update will change."""
    changes: list[str] = []
    if request.stock_adjustment_number is not None:
        changes.append(f"- stock_adjustment_number → {request.stock_adjustment_number}")
    if request.stock_adjustment_date is not None:
        changes.append(
            f"- stock_adjustment_date → {request.stock_adjustment_date.isoformat()}"
        )
    if request.location_id is not None:
        changes.append(f"- location_id → {request.location_id}")
    if request.reason is not None:
        changes.append(f"- reason → {request.reason}")
    if request.additional_info is not None:
        changes.append(f"- additional_info → {request.additional_info}")
    if not changes:
        return "No field changes supplied."
    return "\n".join(changes)


async def _update_stock_adjustment_impl(
    request: UpdateStockAdjustmentParams, context: Context
) -> UpdateStockAdjustmentResponse:
    """Update a stock adjustment with preview/apply safety pattern."""
    from katana_public_api_client.api.stock_adjustment import (
        update_stock_adjustment as api_update_stock_adjustment,
    )
    from katana_public_api_client.models import (
        UpdateStockAdjustmentRequest as APIUpdateStockAdjustmentRequest,
    )
    from katana_public_api_client.utils import unwrap_as

    changes_summary = _format_changes_summary(request)

    # Fail fast if caller didn't supply any updatable field.
    has_changes = any(
        v is not None
        for v in (
            request.stock_adjustment_number,
            request.stock_adjustment_date,
            request.location_id,
            request.reason,
            request.additional_info,
        )
    )
    if not has_changes:
        raise ValueError(
            "At least one updatable field must be provided "
            "(stock_adjustment_number, stock_adjustment_date, location_id, "
            "reason, additional_info)"
        )

    # Preview mode — no API call.
    if request.preview:
        logger.info(
            "stock_adjustment_update_preview",
            id=request.id,
        )
        return UpdateStockAdjustmentResponse(
            id=request.id,
            is_preview=True,
            stock_adjustment_number=request.stock_adjustment_number,
            location_id=request.location_id,
            stock_adjustment_date=request.stock_adjustment_date.isoformat()
            if request.stock_adjustment_date
            else None,
            reason=request.reason,
            additional_info=request.additional_info,
            changes_summary=changes_summary,
            message=(
                f"Preview — call again with preview=false to update stock "
                f"adjustment {request.id}"
            ),
            katana_url=katana_web_url("stock_adjustment", request.id),
        )

    services = get_services(context)

    # Pre-fetch only when echo might be needed (caller didn't supply
    # additional_info) so the common-case PATCH stays a single round trip.
    # ``raise_on_error=False`` keeps the workaround best-effort: if the
    # pre-fetch fails (transient 5xx, permission gap, etc.) we treat it
    # as "no existing snapshot" rather than aborting the user's actual
    # update. Worst case the wipe still fires; the caller's intended
    # write still lands. See :func:`patch_additional_info` for the
    # workaround story.
    existing_info_field: str | None | Unset = UNSET
    if request.additional_info is None:
        existing_response = await get_all_stock_adjustments.asyncio_detailed(
            client=services.client, ids=[request.id]
        )
        existing_rows = unwrap_data(existing_response, raise_on_error=False, default=[])
        if existing_rows:
            existing_info_field = existing_rows[0].additional_info

    api_request = APIUpdateStockAdjustmentRequest(
        stock_adjustment_number=to_unset(request.stock_adjustment_number),
        stock_adjustment_date=to_unset(request.stock_adjustment_date),
        location_id=to_unset(request.location_id),
        reason=to_unset(request.reason),
        additional_info=patch_additional_info(
            request.additional_info, existing_info_field
        ),
    )

    response = await api_update_stock_adjustment.asyncio_detailed(
        id=request.id, client=services.client, body=api_request
    )

    from katana_public_api_client.models import StockAdjustment

    try:
        updated = unwrap_as(response, StockAdjustment)
    except Exception as e:
        logger.error(
            "stock_adjustment_update_failed",
            id=request.id,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise

    logger.info(
        "stock_adjustment_updated",
        id=updated.id,
    )

    return UpdateStockAdjustmentResponse(
        id=updated.id,
        is_preview=False,
        stock_adjustment_number=updated.stock_adjustment_number,
        location_id=updated.location_id,
        stock_adjustment_date=iso_or_none(
            unwrap_unset(updated.stock_adjustment_date, None)
        ),
        reason=unwrap_unset(updated.reason, None),
        additional_info=unwrap_unset(updated.additional_info, None),
        changes_summary=changes_summary,
        message=f"Stock adjustment {updated.id} updated successfully",
        katana_url=katana_web_url("stock_adjustment", updated.id),
    )


@observe_tool
@unpack_pydantic_params
async def update_stock_adjustment(
    request: Annotated[UpdateStockAdjustmentParams, Unpack()], context: Context
) -> ToolResult:
    """Update an existing stock adjustment's header fields.

    Two-step flow: `preview=true` (default) returns a preview of the changes,
    `preview=false` prompts the user for confirmation and applies the update
    via PATCH. At least one updatable field must be supplied
    (stock_adjustment_number, stock_adjustment_date, location_id, reason,
    additional_info). Row-level changes are not supported — create a new
    adjustment for that.
    """
    from katana_mcp.tools.prefab_ui import build_stock_adjustment_update_ui
    from katana_mcp.tools.tool_result_utils import make_tool_result

    response = await _update_stock_adjustment_impl(request, context)
    ui = build_stock_adjustment_update_ui(
        response.model_dump(),
        confirm_request=request,
        confirm_tool="update_stock_adjustment",
    )
    return make_tool_result(response, ui=ui)


# ============================================================================
# Tool 7: delete_stock_adjustment
# ============================================================================


class DeleteStockAdjustmentRequest(BaseModel):
    """Request to delete an existing stock adjustment."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Stock adjustment ID to delete")
    preview: bool = Field(
        default=True,
        description="If true (default), returns a preview. If false, deletes the adjustment.",
    )


class DeleteStockAdjustmentResponse(BaseModel):
    """Response from deleting a stock adjustment."""

    id: int
    is_preview: bool
    stock_adjustment_number: str | None
    location_id: int | None
    row_count: int
    message: str


async def _delete_stock_adjustment_impl(
    request: DeleteStockAdjustmentRequest, context: Context
) -> DeleteStockAdjustmentResponse:
    """Delete a stock adjustment with preview/apply safety pattern.

    Preview mode fetches the adjustment (via the list endpoint filter) so the
    caller can see what will be removed before applying. Apply mode calls the
    API's DELETE endpoint, which reverses the associated inventory changes.
    """
    from katana_public_api_client.api.stock_adjustment import (
        delete_stock_adjustment as api_delete_stock_adjustment,
        get_all_stock_adjustments,
    )
    from katana_public_api_client.utils import is_success, unwrap, unwrap_data

    services = get_services(context)

    # Look up what we're about to delete so preview + final response include
    # enough detail for the user to sanity-check the action. Katana does not
    # expose GET /stock_adjustments/{id}, so we filter the list endpoint by id.
    list_response = await get_all_stock_adjustments.asyncio_detailed(
        client=services.client,
        ids=[request.id],
        limit=1,
        page=1,  # Explicit page disables auto-pagination — one HTTP call suffices.
    )
    matches = unwrap_data(list_response, default=[])
    existing = next((adj for adj in matches if adj.id == request.id), None)

    if existing is None:
        raise ValueError(f"Stock adjustment {request.id} not found")

    rows = unwrap_unset(existing.stock_adjustment_rows, [])
    row_count = len(rows)
    stock_adjustment_number = existing.stock_adjustment_number
    location_id = existing.location_id

    if request.preview:
        logger.info(
            "stock_adjustment_delete_preview",
            id=request.id,
            row_count=row_count,
        )
        return DeleteStockAdjustmentResponse(
            id=request.id,
            is_preview=True,
            stock_adjustment_number=stock_adjustment_number,
            location_id=location_id,
            row_count=row_count,
            message=(
                f"Preview — call again with preview=false to delete stock "
                f"adjustment {stock_adjustment_number} "
                f"({row_count} row{'s' if row_count != 1 else ''})"
            ),
        )

    response = await api_delete_stock_adjustment.asyncio_detailed(
        id=request.id, client=services.client
    )

    if not is_success(response):
        # unwrap raises a typed APIError/ValidationError/etc with a clean message.
        unwrap(response)

    logger.info(
        "stock_adjustment_deleted",
        id=request.id,
        stock_adjustment_number=stock_adjustment_number,
    )

    return DeleteStockAdjustmentResponse(
        id=request.id,
        is_preview=False,
        stock_adjustment_number=stock_adjustment_number,
        location_id=location_id,
        row_count=row_count,
        message=(
            f"Stock adjustment {stock_adjustment_number} (id={request.id}) "
            "deleted; associated inventory movements reversed"
        ),
    )


@observe_tool
@unpack_pydantic_params
async def delete_stock_adjustment(
    request: Annotated[DeleteStockAdjustmentRequest, Unpack()], context: Context
) -> ToolResult:
    """Delete a stock adjustment by ID.

    Two-step flow: `preview=true` (default) returns a preview (including the
    adjustment number, location, and row count that would be affected);
    `preview=false` prompts the user for confirmation, then calls DELETE.
    Deleting a stock adjustment reverses the associated inventory movements.
    """
    from katana_mcp.tools.prefab_ui import build_stock_adjustment_delete_ui
    from katana_mcp.tools.tool_result_utils import make_tool_result

    response = await _delete_stock_adjustment_impl(request, context)
    ui = build_stock_adjustment_delete_ui(
        response.model_dump(),
        confirm_request=request,
        confirm_tool="delete_stock_adjustment",
    )
    return make_tool_result(response, ui=ui)


def register_tools(mcp: FastMCP) -> None:
    """Register all inventory tools with the FastMCP instance.

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
        readOnlyHint=False,
        destructiveHint=False,
        openWorldHint=True,
    )

    _destructive_write = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        openWorldHint=True,
    )

    mcp.tool(tags={"inventory", "read"}, annotations=_read, meta=UI_META)(
        check_inventory
    )
    mcp.tool(tags={"inventory", "read"}, annotations=_read, meta=UI_META)(
        list_low_stock_items
    )
    mcp.tool(tags={"inventory", "read"}, annotations=_read)(get_inventory_movements)
    mcp.tool(tags={"inventory", "read"}, annotations=_read, meta=UI_META)(inventory_at)
    mcp.tool(tags={"inventory", "read"}, annotations=_read)(list_stock_adjustments)
    register_preview_tool(
        mcp,
        create_stock_adjustment,
        tags={"inventory", "write"},
        annotations=_create,
        meta=UI_META,
    )
    register_preview_tool(
        mcp,
        update_stock_adjustment,
        tags={"inventory", "write"},
        annotations=_destructive_write,
        meta=UI_META,
    )
    register_preview_tool(
        mcp,
        delete_stock_adjustment,
        tags={"inventory", "write"},
        annotations=_destructive_write,
        meta=UI_META,
    )
