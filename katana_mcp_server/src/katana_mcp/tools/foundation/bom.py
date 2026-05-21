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
from katana_mcp.tools.tool_result_utils import UI_META, make_json_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params
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
from katana_public_api_client.models_pydantic._generated import CachedVariant
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
    """Response containing BOM rows for a product variant."""

    product_variant_id: int
    rows: list[BomRowInfo]
    total_count: int


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
    return GetProductBomResponse(
        product_variant_id=request.product_variant_id,
        rows=rows,
        total_count=len(rows),
    )


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
    response = await _get_product_bom_impl(request, context)
    return make_json_result(response)


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
    async def apply() -> None:
        # ``POST /bom_rows`` returns 204 No Content per Katana's spec — no
        # response body to parse. The previous ``unwrap_as(response, BomRow)``
        # call raised ``APIError`` on every successful create because
        # ``unwrap`` treated ``parsed is None`` as an error regardless of
        # status, fail-fast halted the plan, and a multi-row batch silently
        # became a 1-row commit (#809). Mirror ``_make_delete_bom_row_apply``:
        # confirm 2xx, otherwise let ``unwrap`` raise the typed error.
        response = await api_create_bom_row.asyncio_detailed(
            client=services.client, body=body
        )
        if not is_success(response):
            unwrap(response)
        return None

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
    try:
        existing_rows = await _fetch_bom_row_infos(services, request.id)
        existing_snapshot: GetProductBomResponse | None = GetProductBomResponse(
            product_variant_id=request.id,
            rows=existing_rows,
            total_count=len(existing_rows),
        )
    except asyncio.CancelledError:
        # Never swallow cooperative cancellation — request timeouts and
        # shutdown have to propagate cleanly.
        raise
    except Exception:
        existing_snapshot = None

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
    return await run_modify_plan(
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
    )


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
