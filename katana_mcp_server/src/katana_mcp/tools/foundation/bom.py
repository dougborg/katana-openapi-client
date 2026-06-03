"""Product-level BOM (Bill of Materials) tools for Katana MCP Server.

Tools:
- get_product_bom: list BOM rows for a producible product variant.
- manage_product_bom: add / update / delete BOM rows on a variant with
  the standard preview/apply two-step gate.

BOM rows are **variant-scoped** in Katana — the parent identifier is a
``product_variant_id`` (not just a product id). Producible products
without variants still have a single variant; pass that variant's id.

Manufacturing-order recipe rows (``modify_manufacturing_order``'s
``add_recipe_rows`` / ``update_recipe_rows`` / ``delete_recipe_row_ids``)
are a *snapshot* copied from the product master at MO creation. These
BOM tools edit the master that future MOs are copied from.
"""

from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field, model_validator

from katana_mcp.logging import observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools._modification import (
    ConfirmableRequest,
    compute_field_diff,
    make_response_verifier,
    to_tool_result,
)
from katana_mcp.tools._modification_dispatch import (
    ActionSpec,
    EntityNaming,
    has_any_subpayload,
    plan_creates,
    run_modify_plan,
    unset_dict,
)
from katana_mcp.tools.tool_result_utils import UI_META, make_tool_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import katana_web_url
from katana_public_api_client.api.bom_row import (
    create_bom_row as api_create_bom_row,
    delete_bom_row as api_delete_bom_row,
    get_all_bom_rows as api_get_all_bom_rows,
    update_bom_row as api_update_bom_row,
)
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    BomRow,
    CreateBomRowRequest as APICreateBomRowRequest,
    UpdateBomRowRequest as APIUpdateBomRowRequest,
)
from katana_public_api_client.models_pydantic._generated import (
    CachedProduct,
    CachedVariant,
)
from katana_public_api_client.utils import is_success, unwrap, unwrap_as, unwrap_data

# ============================================================================
# Shared response shape
# ============================================================================


class BomRowInfo(BaseModel):
    """Full BOM row + resolved ingredient SKU / display_name.

    The id is stringified UUID so the JSON wire shape stays plain text;
    callers pass it back as a string to ``update_bom_rows`` /
    ``delete_bom_row_ids``.
    """

    id: str
    product_item_id: int
    product_variant_id: int
    ingredient_variant_id: int
    sku: str | None = None
    display_name: str | None = None
    quantity: float | None = None
    notes: str | None = None
    rank: int | None = None


# ============================================================================
# Tool 1: get_product_bom
# ============================================================================


class GetProductBomRequest(BaseModel):
    """Request to list BOM rows for a product variant."""

    model_config = ConfigDict(extra="forbid")

    product_variant_id: int = Field(
        ...,
        description=(
            "Product variant ID whose BOM rows to fetch. BOM rows are "
            "variant-scoped — a producible product with multiple variants has "
            "a separate recipe per variant."
        ),
    )


class GetProductBomResponse(BaseModel):
    """Response containing BOM rows for a product variant.

    Carries enough parent-entity context for the Prefab card's tier-1
    identity header (product name + variant SKU + producible badge +
    Katana link) without forcing the agent to issue a follow-up
    ``get_variant_details``. ``product_name`` / ``variant_sku`` etc.
    fall back to ``None`` when the parent variant isn't in the typed
    cache — the card still renders with whatever's available.
    """

    product_variant_id: int
    rows: list[BomRowInfo]
    total_count: int
    product_id: int | None = None
    product_name: str | None = None
    variant_sku: str | None = None
    variant_display_name: str | None = None
    is_producible: bool | None = None
    uom: str | None = None
    katana_url: str | None = None


async def _resolve_ingredient_fields(
    services: Any, variant_ids: set[int]
) -> dict[int, tuple[str | None, str | None]]:
    """Resolve a set of variant_ids to ``{id: (sku, display_name)}`` via cache."""
    variants = await services.typed_cache.catalog.get_many_by_ids(
        CachedVariant, variant_ids, include_deleted=True
    )
    resolved: dict[int, tuple[str | None, str | None]] = {}
    for v_id in variant_ids:
        v = variants.get(v_id)
        if v is None:
            resolved[v_id] = (None, None)
            continue
        if isinstance(v, dict):
            resolved[v_id] = (v.get("sku"), v.get("display_name"))
        else:
            resolved[v_id] = (
                getattr(v, "sku", None),
                getattr(v, "display_name", None),
            )
    return resolved


def _bom_row_info_from_attrs(
    row: BomRow, sku: str | None, display_name: str | None
) -> BomRowInfo:
    """Build BomRowInfo from a generated ``BomRow`` attrs model."""
    return BomRowInfo(
        id=str(row.id),
        product_item_id=row.product_item_id,
        product_variant_id=row.product_variant_id,
        ingredient_variant_id=row.ingredient_variant_id,
        sku=sku,
        display_name=display_name,
        quantity=unwrap_unset(row.quantity, None),
        notes=unwrap_unset(row.notes, None),
        rank=unwrap_unset(row.rank, None),
    )


async def _fetch_bom_rows(services: Any, product_variant_id: int) -> list[BomRow]:
    """Fetch every BOM row for the variant (paginated client transport handles >250)."""
    response = await api_get_all_bom_rows.asyncio_detailed(
        client=services.client,
        product_variant_id=product_variant_id,
        limit=250,
    )
    return unwrap_data(response, default=[])


async def _fetch_bom_row_infos(
    services: Any, product_variant_id: int
) -> list[BomRowInfo]:
    """Fetch BOM rows + enrich each with cached ingredient SKU/display_name."""
    raw_rows = await _fetch_bom_rows(services, product_variant_id)
    ingredient_ids = {row.ingredient_variant_id for row in raw_rows}
    resolved = await _resolve_ingredient_fields(services, ingredient_ids)
    return [
        _bom_row_info_from_attrs(row, *resolved[row.ingredient_variant_id])
        for row in raw_rows
    ]


async def _get_product_bom_impl(
    request: GetProductBomRequest, context: Context
) -> GetProductBomResponse:
    services = get_services(context)
    rows = await _fetch_bom_row_infos(services, request.product_variant_id)

    # Resolve the parent variant + product so the Prefab card's tier-1
    # header has a name to render. Best-effort: a cold cache falls
    # through to the bare wire fields without blocking the response.
    variant, product = await _resolve_parent_for_card(
        services, request.product_variant_id
    )

    return GetProductBomResponse(
        product_variant_id=request.product_variant_id,
        rows=rows,
        total_count=len(rows),
        product_id=getattr(product, "id", None) if product is not None else None,
        product_name=getattr(product, "name", None) if product is not None else None,
        variant_sku=getattr(variant, "sku", None) if variant is not None else None,
        variant_display_name=(
            getattr(variant, "display_name", None) if variant is not None else None
        ),
        is_producible=(
            getattr(product, "is_producible", None) if product is not None else None
        ),
        uom=getattr(product, "uom", None) if product is not None else None,
        katana_url=(
            katana_web_url("product", product.id)
            if product is not None and getattr(product, "id", None) is not None
            else None
        ),
    )


async def _resolve_parent_for_card(
    services: Any, product_variant_id: int
) -> tuple[Any | None, Any | None]:
    """Look up the variant and its parent product for card display.

    Returns ``(variant, product)`` — either may be ``None`` if the
    cache misses or the parent is a material (BOMs can hang off
    materials too, but the typical case is a producible product).
    Best-effort: cache failures fall through to ``(None, None)`` so
    the card still renders with whatever fields are available.

    Cooperative cancellation (``asyncio.CancelledError``) is re-raised
    explicitly — request timeouts and shutdown must propagate cleanly,
    not be swallowed by the best-effort fallback. Matches the existing
    snapshot path in ``_modify_product_bom_impl``.
    """
    try:
        variants = await services.typed_cache.catalog.get_many_by_ids(
            CachedVariant, {product_variant_id}, include_deleted=True
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        return None, None
    variant = variants.get(product_variant_id) if variants else None
    if variant is None:
        return None, None

    product_id = (
        variant.get("product_id")
        if isinstance(variant, dict)
        else getattr(variant, "product_id", None)
    )
    if product_id is None:
        return variant, None

    try:
        product = await services.typed_cache.catalog.get_by_id(
            CachedProduct, product_id, include_deleted=True
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        return variant, None
    return variant, product


@observe_tool
@unpack_pydantic_params
async def get_product_bom(
    request: Annotated[GetProductBomRequest, Unpack()],
    context: Context,
) -> ToolResult:
    """List the BOM (Bill of Materials) rows for a producible product variant.

    BOM rows are **variant-scoped** — a producible product with multiple
    variants has a separate recipe per variant. Pass the specific
    ``product_variant_id``. For multi-variant products, call once per
    variant.

    Returns every field on each ``BomRow`` (id, product_item_id,
    product_variant_id, ingredient_variant_id, quantity, notes, rank)
    plus the resolved ingredient SKU and Katana-UI display_name (looked
    up from the typed cache). Use this before calling ``manage_product_bom``
    so you can identify rows to update or delete (the row ``id`` is a UUID
    string).

    Returns an empty rows list (``total_count: 0``) when the variant has
    no recipe — distinct from "variant not found" (which surfaces no
    error here, since the API returns zero rows for both cases). Use
    ``get_variant_details`` first to confirm the variant exists and is
    ``is_producible``.
    """
    from katana_mcp.tools.prefab_ui import build_product_bom_ui

    response = await _get_product_bom_impl(request, context)
    return make_tool_result(response, ui=build_product_bom_ui(response.model_dump()))


# ============================================================================
# Tool 2: manage_product_bom (preview/apply)
# ============================================================================


class BomOperation(StrEnum):
    """Operation names emitted on ActionSpecs by ``manage_product_bom``."""

    ADD_BOM_ROW = "add_bom_row"
    UPDATE_BOM_ROW = "update_bom_row"
    DELETE_BOM_ROW = "delete_bom_row"


class BomRowAdd(BaseModel):
    """A new BOM row to attach to the product variant.

    Katana derives ``product_item_id`` from the parent variant; this tool
    looks it up automatically from the typed cache. Callers only need to
    supply the *ingredient* and its quantity.
    """

    model_config = ConfigDict(extra="forbid")

    ingredient_variant_id: int = Field(
        ...,
        description="Variant ID of the ingredient consumed by this BOM row.",
    )
    quantity: float | None = Field(
        default=None,
        ge=0,
        description=(
            "Quantity of the ingredient consumed per one unit of the parent "
            "variant produced (e.g. 2 for two spokes per kit). Optional — "
            "Katana accepts BOM rows without a quantity, used for placeholder "
            "or annotation rows."
        ),
    )
    notes: str | None = Field(
        default=None,
        description="Free-form notes attached to this BOM row.",
    )


class BomRowUpdate(BaseModel):
    """A patch to an existing BOM row.

    Only ``ingredient_variant_id``, ``quantity``, and ``notes`` are
    patchable — ``rank`` is server-managed (Katana reorders rows
    internally) and ``product_item_id`` / ``product_variant_id`` would
    move the row to a different recipe (forbidden via the update
    endpoint).
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(..., description="BOM row UUID (from get_product_bom).")
    ingredient_variant_id: int | None = Field(
        default=None,
        description="Swap the ingredient for a different variant.",
    )
    quantity: float | None = Field(
        default=None,
        ge=0,
        description="New quantity-per-unit value.",
    )
    notes: str | None = Field(
        default=None,
        description="New notes value (overwrites the existing notes string).",
    )

    @model_validator(mode="after")
    def _require_at_least_one_patch_field(self) -> BomRowUpdate:
        """A patch with only ``id`` set is a no-op and would yield an
        empty PATCH body → generic Katana 422. The dispatcher's
        empty-diff guard catches this too, but pinning it at the request
        boundary gives the caller a clearer error before any plan is
        built.
        """
        if (
            self.ingredient_variant_id is None
            and self.quantity is None
            and self.notes is None
        ):
            raise ValueError(
                "BomRowUpdate requires at least one of "
                "ingredient_variant_id, quantity, or notes to be set."
            )
        return self


class ManageProductBomRequest(ConfirmableRequest):
    """Unified BOM modification request for a product variant.

    Sub-payloads (any subset, all optional): ``add_bom_rows`` /
    ``update_bom_rows`` / ``delete_bom_row_ids``. Actions execute in
    canonical order (adds → updates → deletes) and the dispatcher fails
    fast on the first error.

    The inherited ``id`` field carries the **parent ``product_variant_id``**
    — BOM rows are variant-scoped, not product-scoped. For multi-variant
    products, call this tool once per variant.
    """

    id: int = Field(
        ...,
        description=(
            "Product variant ID — the parent that owns the BOM rows. "
            "BOM rows are variant-scoped."
        ),
    )
    add_bom_rows: list[BomRowAdd] | None = Field(
        default=None,
        description=(
            "New BOM rows to attach to the variant. Each: "
            "ingredient_variant_id (required), quantity, notes."
        ),
    )
    update_bom_rows: list[BomRowUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing BOM rows. Each entry: id (UUID, required) + "
            "any subset of ingredient_variant_id, quantity, notes."
        ),
    )
    delete_bom_row_ids: list[UUID] | None = Field(
        default=None,
        description="BOM row UUIDs to delete from the recipe.",
    )


# ----------------------------------------------------------------------------
# Helpers — parent resolution + per-action apply closures
# ----------------------------------------------------------------------------


async def _resolve_product_item_id(services: Any, variant_id: int) -> int:
    """Look up the parent product/material id for a variant.

    BOM rows require both ``product_item_id`` and ``product_variant_id``
    in the create payload. The variant's parent id is either
    ``product_id`` or ``material_id`` on ``CachedVariant`` (only one is
    set per row). Raises ``ValueError`` with a clear message when the
    variant isn't cached or has no parent — that's the only case the
    tool can't recover from on its own.
    """
    variants = await services.typed_cache.catalog.get_many_by_ids(
        CachedVariant, {variant_id}, include_deleted=True
    )
    v = variants.get(variant_id)
    if v is None:
        raise ValueError(
            f"Variant {variant_id} not found in catalog. Confirm the id with "
            "search_items or get_variant_details before calling manage_product_bom."
        )
    if isinstance(v, dict):
        product_id = v.get("product_id")
        material_id = v.get("material_id")
    else:
        product_id = getattr(v, "product_id", None)
        material_id = getattr(v, "material_id", None)
    parent = product_id or material_id
    if parent is None:
        raise ValueError(
            f"Variant {variant_id} has neither a parent product nor material "
            "— BOM rows require a parent item."
        )
    return parent


def _build_create_bom_row_request(
    product_item_id: int, product_variant_id: int, row: BomRowAdd
) -> APICreateBomRowRequest:
    return APICreateBomRowRequest(
        product_item_id=product_item_id,
        product_variant_id=product_variant_id,
        ingredient_variant_id=row.ingredient_variant_id,
        quantity=to_unset(row.quantity),
        notes=to_unset(row.notes),
    )


def _build_update_bom_row_request(patch: BomRowUpdate) -> APIUpdateBomRowRequest:
    return APIUpdateBomRowRequest(
        **unset_dict(patch, exclude=("id",)),
    )


def _make_create_bom_row_apply(services: Any, body: APICreateBomRowRequest):
    async def apply() -> BomRow:
        # ``POST /bom_rows`` returns ``200`` with the full ``BomRow`` body
        # (verified live, 2026-05-22 — see #820). Our spec previously declared
        # ``204 No Content``, so the generated parser had no 200 branch and
        # ``unwrap_as(response, BomRow)`` raised ``APIError`` on every
        # successful create (``parsed is None``), fail-fast halted the plan,
        # and a multi-row batch silently became a 1-row commit (#809). With the
        # spec aligned to the real 200+body shape, ``unwrap_as`` now parses the
        # row cleanly and we return it so the new id / created_at / rank flow
        # into the dispatcher's ``apply_outcome`` for downstream consumers.
        response = await api_create_bom_row.asyncio_detailed(
            client=services.client, body=body
        )
        return unwrap_as(response, BomRow)

    return apply


def _make_update_bom_row_apply(
    services: Any, row_id: UUID, body: APIUpdateBomRowRequest
):
    async def apply() -> BomRow:
        response = await api_update_bom_row.asyncio_detailed(
            id=row_id, client=services.client, body=body
        )
        return unwrap_as(response, BomRow)

    return apply


def _make_delete_bom_row_apply(services: Any, row_id: UUID):
    async def apply() -> None:
        response = await api_delete_bom_row.asyncio_detailed(
            id=row_id, client=services.client
        )
        if not is_success(response):
            unwrap(response)
        return None

    return apply


# ----------------------------------------------------------------------------
# _impl
# ----------------------------------------------------------------------------


def _collect_ingredient_ids(
    request: ManageProductBomRequest,
    existing_snapshot: GetProductBomResponse | None,
) -> set[int]:
    """Union of every ingredient_variant_id touched by the plan.

    Adds + updates contribute their request-side ingredient id (when the
    update swaps the ingredient). Updates + deletes also contribute the
    *existing* row's ingredient id (resolved via the snapshot) so the
    builder can render the pre-patch identity. Falls back gracefully
    when the snapshot is None (skip the existing-row contributions).
    """
    ids: set[int] = set()
    for add in request.add_bom_rows or []:
        ids.add(add.ingredient_variant_id)
    for patch in request.update_bom_rows or []:
        if patch.ingredient_variant_id is not None:
            ids.add(patch.ingredient_variant_id)
    if existing_snapshot is not None:
        rows_by_id = {row.id: row for row in existing_snapshot.rows}
        for patch in request.update_bom_rows or []:
            row = rows_by_id.get(str(patch.id))
            if row is not None:
                ids.add(row.ingredient_variant_id)
        for row_id in request.delete_bom_row_ids or []:
            row = rows_by_id.get(str(row_id))
            if row is not None:
                ids.add(row.ingredient_variant_id)
    return ids


async def _modify_product_bom_impl(request: ManageProductBomRequest, context: Context):
    services = get_services(context)

    if not has_any_subpayload(request):
        raise ValueError(
            "At least one sub-payload must be set: add_bom_rows, "
            "update_bom_rows, or delete_bom_row_ids."
        )

    # Snapshot the existing BOM so ``run_modify_plan`` can populate
    # ``prior_state`` for manual revert if the plan partially applies
    # (fail-fast halts after the first error). Best-effort: a list
    # failure shouldn't block the modify call itself.
    #
    # Also resolve the parent variant + product (same path
    # ``_get_product_bom_impl`` uses) so the modify card's tier-1 header
    # carries ``product_name``, ``variant_sku``, ``uom`` and a
    # ``katana_url``. Without these the card falls back to a bare
    # "BOM for variant {id}" header — usable but not user-identifiable.
    #
    # The row-fetch and parent-resolution failure modes are independent
    # (split try blocks): a typed-cache miss on the parent shouldn't
    # discard rows we already successfully listed (loses diff context +
    # revert reference). Each call falls back to its own degraded state:
    # row-fetch failure → ``existing_snapshot=None`` (the dispatcher
    # warns "could not fetch"); parent-resolution failure → snapshot
    # with rows + None header fields (card renders the placeholder
    # title but the table + revert reference stay intact).
    existing_rows: list[BomRowInfo] | None = None
    try:
        existing_rows = await _fetch_bom_row_infos(services, request.id)
    except asyncio.CancelledError:
        # Never swallow cooperative cancellation — request timeouts and
        # shutdown have to propagate cleanly.
        raise
    except Exception:
        existing_rows = None

    existing_snapshot: GetProductBomResponse | None
    if existing_rows is None:
        existing_snapshot = None
    else:
        try:
            variant, product = await _resolve_parent_for_card(services, request.id)
        except asyncio.CancelledError:
            raise
        except Exception:
            variant, product = None, None
        existing_snapshot = GetProductBomResponse(
            product_variant_id=request.id,
            rows=existing_rows,
            total_count=len(existing_rows),
            product_id=(getattr(product, "id", None) if product is not None else None),
            product_name=(
                getattr(product, "name", None) if product is not None else None
            ),
            variant_sku=(
                getattr(variant, "sku", None) if variant is not None else None
            ),
            variant_display_name=(
                getattr(variant, "display_name", None) if variant is not None else None
            ),
            is_producible=(
                getattr(product, "is_producible", None) if product is not None else None
            ),
            uom=getattr(product, "uom", None) if product is not None else None,
            katana_url=(
                katana_web_url("product", product.id)
                if product is not None and getattr(product, "id", None) is not None
                else None
            ),
        )

    # Adds need the parent product/material id; fetch once if needed.
    product_item_id: int | None = None
    if request.add_bom_rows:
        product_item_id = await _resolve_product_item_id(services, request.id)

    plan: list[ActionSpec] = []

    # Adds.
    if request.add_bom_rows and product_item_id is not None:
        # Bind product_item_id at closure-build time so the body builder
        # doesn't capture a possibly-None typed var inside the lambda.
        parent_id = product_item_id
        plan.extend(
            plan_creates(
                request.add_bom_rows,
                BomOperation.ADD_BOM_ROW,
                lambda row: _build_create_bom_row_request(parent_id, request.id, row),
                lambda body: _make_create_bom_row_apply(services, body),
            )
        )

    # Updates — UUID-keyed, so the shared ``plan_updates`` helper (which
    # types target_id as int and uses asyncio.gather on int ids) doesn't
    # fit. Hand-build ActionSpecs: no fetcher (no get-by-id endpoint
    # exposed for individual rows — list-filter only), so every diff is
    # marked unknown_prior.
    for patch in request.update_bom_rows or []:
        body = _build_update_bom_row_request(patch)
        diff = compute_field_diff(None, patch, unknown_prior=True)
        plan.append(
            ActionSpec(
                operation=BomOperation.UPDATE_BOM_ROW,
                target_id=str(patch.id),
                diff=diff,
                apply=_make_update_bom_row_apply(services, patch.id, body),
                verify=make_response_verifier(diff),
            )
        )

    # Deletes.
    for row_id in request.delete_bom_row_ids or []:
        plan.append(
            ActionSpec(
                operation=BomOperation.DELETE_BOM_ROW,
                target_id=str(row_id),
                diff=[],
                apply=_make_delete_bom_row_apply(services, row_id),
                verify=None,
            )
        )

    # Resolve ingredient SKU / display_name for every variant id touched
    # by the plan so ``build_bom_modify_ui`` can render user-facing row
    # identities on *added* rows (the prior_state snapshot already
    # resolves SKUs for existing rows via ``_fetch_bom_row_infos``). One
    # batched cache lookup; misses degrade to ``(None, None)``.
    ingredient_ids = _collect_ingredient_ids(request, existing_snapshot)
    resolved_pairs = (
        await _resolve_ingredient_fields(services, ingredient_ids)
        if ingredient_ids
        else {}
    )
    # Flatten the (sku, display_name) tuple into a serializable dict so
    # the wire shape carries through ``model_dump`` cleanly and the
    # renderer reads typed string fields.
    resolved_ingredients: dict[int, dict[str, str | None]] = {
        vid: {"sku": sku, "display_name": display_name}
        for vid, (sku, display_name) in resolved_pairs.items()
    }

    # No web URL for variant-scoped BOMs (Katana's URL pattern is
    # /product/{id} on the product id, not the variant id; the BOM tab
    # is reached by navigating from the product page). Skip katana_url
    # — agents don't need it to operate; users land on the product page
    # by other means.
    #
    # ``entity_type="product_bom"`` (not ``"bom_row"``) so the
    # dispatcher's labels match ``entity_id=product_variant_id`` — the
    # whole BOM is the entity being modified; individual rows are the
    # per-action ``operation`` targets.
    response = await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="product_bom",
            entity_label=f"BOM for product variant {request.id}",
            tool_name="manage_product_bom",
        ),
        web_url_kind=None,
        existing=existing_snapshot,
        plan=plan,
        # The list-by-variant endpoint is the read path used to populate
        # ``existing_snapshot`` above. A failed list silently falls
        # through to ``existing_snapshot=None`` — the dispatcher's
        # "could not fetch" warning is informative when that happens.
        has_get_endpoint=True,
        cache_merge=None,
        # Thread the resolved ingredients map onto the response so
        # ``build_bom_modify_ui`` can render added-row SKUs + display
        # names without a second cache hit at render time.
        extras={"resolved_ingredients": resolved_ingredients},
    )

    # On the apply path, precompute the post-apply DataTable rows + the
    # apply-outcome chrome (Tier-1 header Badge label/variant, failed-
    # row Alert summary) and stuff into ``response.extras``. From there
    # the apply-time call to ``build_bom_modify_ui`` seeds these into
    # its OWN PrefabApp ``state.*`` slots, and the preview iframe's
    # ``on_success`` SetState chain reads off ``{{ $result.state.<slot> }}``
    # (the apply tool's wire envelope is keyed by ``$prefab`` / ``view``
    # / ``state`` — not ``extras`` — which is why ``$result.state`` is
    # the correct path; documented in
    # ``test_apply_button_morphs_card_to_applied_state``).
    #
    # The slots that flow extras → state → preview-morph:
    #
    # - ``applied_plan_rows`` — DataTable row dicts with per-row
    #   APPLIED / FAILED Status decoration.
    # - ``applied_outcome_label`` — Tier-1 state Badge text
    #   (APPLIED / PARTIAL FAILURE / FAILED). Without this the badge
    #   would stay frozen on the preview-time "APPLIED" default even
    #   when actions failed.
    # - ``applied_outcome_variant`` — pairs with the label so the
    #   renderer picks ``default`` vs ``destructive`` based on the
    #   actual outcome.
    # - ``applied_failed_count`` / ``applied_failed_summary`` — drives
    #   the consolidated failed-row Alert in the morphed state. We
    #   pre-format the summary string server-side (one line per failed
    #   row) because Prefab's Alert children are fixed at build time —
    #   a state-driven list of AlertDescription rows is not expressible
    #   in the current component vocabulary.
    #
    # Domain helpers live in ``foundation.bom_table`` (#850) — no
    # cross-import from ``prefab_ui`` here. The rendering layer imports
    # the same helpers; the table-merge math is shared.
    if not response.is_preview:
        from katana_mcp.tools.foundation.bom_table import (
            _merge_bom_rows_for_modify_card,
            _prepare_bom_table_rows,
            _summarize_apply_outcome,
        )

        # ``execute_plan`` is fail-fast: ``response.actions`` ends at the
        # first failed action; plan entries past that point are never
        # attempted and so don't appear in ``response.actions``. Without
        # synthesizing them here the morphed table would silently HIDE
        # the never-run rows — the user sees "1 succeeded, 1 failed" but
        # the original plan was "1 succeeded, 1 failed, 3 not run". The
        # not-run rows still belong on the table so the operator knows
        # what's still pending. We synthesize ``succeeded=None`` entries
        # for the plan tail (matches the preview "PLANNED" status, which
        # is correct semantically — those rows ARE still planned).
        executed_results = list(response.actions)
        not_run_specs = plan[len(executed_results) :]
        not_run_actions = [
            {
                "operation": spec.operation,
                "target_id": spec.target_id,
                "succeeded": None,
                "error": None,
                "changes": [
                    c.model_dump() if hasattr(c, "model_dump") else dict(c)
                    for c in spec.diff
                ],
                "status_label": "NOT RUN",
            }
            for spec in not_run_specs
        ]
        actions_dicts = [a.model_dump() for a in executed_results] + not_run_actions
        merged = _merge_bom_rows_for_modify_card(
            response.prior_state, actions_dicts, resolved_ingredients
        )
        applied_plan_rows = _prepare_bom_table_rows(merged)
        # Summarize against the EXECUTED actions only — "PARTIAL FAILURE"
        # vs "FAILED" buckets on what was attempted, not the full plan.
        outcome_label, outcome_variant = _summarize_apply_outcome(
            [a.model_dump() for a in executed_results]
        )
        failed_rows = [
            r for r in applied_plan_rows if r.get("status_label") == "FAILED"
        ]
        failed_summary_lines: list[str] = []
        for r in failed_rows:
            sku = r.get("sku") or f"variant {r.get('ingredient_variant_id')}"
            err = r.get("error") or "unknown error"
            failed_summary_lines.append(f"Failed — {sku}: {err}")
        if not_run_specs:
            failed_summary_lines.append(
                f"({len(not_run_specs)} planned action(s) NOT RUN — "
                f"fail-fast halted the plan; re-issue manage_product_bom "
                f"after fixing the failure to apply the remaining changes.)"
            )
        # Footer ``applied_verb`` mirrors the Tier-1 outcome label so the
        # in-place morph after Confirm reads the right verb instead of
        # the build-time "applied" default. See the comment in
        # ``build_bom_modify_ui``'s ``extra_on_success`` for the path.
        verb_map = {
            "APPLIED": "applied",
            "FAILED": "failed",
            "PARTIAL FAILURE": "partially applied",
        }
        response.extras["applied_plan_rows"] = applied_plan_rows
        response.extras["applied_outcome_label"] = outcome_label
        response.extras["applied_outcome_variant"] = outcome_variant
        response.extras["applied_failed_count"] = len(failed_rows)
        response.extras["applied_failed_summary"] = "\n".join(failed_summary_lines)
        response.extras["applied_verb"] = verb_map.get(outcome_label, "applied")

    return response


@observe_tool
@unpack_pydantic_params
async def manage_product_bom(
    request: Annotated[ManageProductBomRequest, Unpack()], context: Context
) -> ToolResult:
    """Add / update / delete BOM rows on a producible product variant.

    BOM rows are **variant-scoped** — pass the parent ``product_variant_id``
    as ``id``. For multi-variant products, call this tool once per
    variant.

    Sub-payloads (any subset, all optional):

    - ``add_bom_rows`` — new ingredient rows. Each carries
      ``ingredient_variant_id`` (required) + ``quantity`` and ``notes``.
      The tool resolves the parent ``product_item_id`` automatically from
      the typed cache, so callers don't need to pass it.
    - ``update_bom_rows`` — patches to existing rows. Each: ``id`` (UUID)
      + any subset of ``ingredient_variant_id``, ``quantity``, ``notes``.
      Look up the row id with ``get_product_bom`` first. ``rank`` is
      server-managed and not patchable.
    - ``delete_bom_row_ids`` — UUIDs of rows to remove.

    Two-step flow: ``preview=true`` (default) returns a per-action
    preview; ``preview=false`` executes the plan. Fail-fast: the first
    failed action halts the plan; later actions are not attempted.

    Each action's diff is marked ``is_unknown_prior=true`` because BOM
    rows have no individual GET-by-id endpoint (only the list-filter
    endpoint). Call ``get_product_bom`` after a successful apply to see
    the post-state.
    """
    response = await _modify_product_bom_impl(request, context)
    return to_tool_result(
        response,
        confirm_request=request,
        confirm_tool="manage_product_bom",
    )


# ============================================================================
# Registration
# ============================================================================


def register_tools(mcp: FastMCP) -> None:
    """Register BOM tools with the FastMCP instance."""
    from mcp.types import ToolAnnotations

    from katana_mcp.tools.prefab_ui import register_preview_tool

    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
    _modify = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )

    mcp.tool(tags={"catalog", "read"}, annotations=_read, meta=UI_META)(get_product_bom)
    register_preview_tool(
        mcp,
        manage_product_bom,
        tags={"catalog", "write"},
        annotations=_modify,
        meta=UI_META,
    )
