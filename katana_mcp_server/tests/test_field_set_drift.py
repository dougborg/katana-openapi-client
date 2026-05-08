"""Field-set drift detector — closes #519.

For every MCP-layer Pydantic request model paired with its underlying
generated API attrs request model, asserts:

    set(api_field_names) - allowed_drops  is a subset of  set(mcp_field_names) union renames

This catches the "MCP request model is narrower than API attrs counterpart"
bug class — the recurring issue (#503, #505, #518, #605, all consolidated
under the #627 sweep) where pydantic silently drops caller-supplied fields
because the MCP model never declared them. PR #514's ``extra="forbid"``
catches typos; this test catches *under-modeling*.

When a regen adds a new field to the API attrs class, this test fails and
forces a deliberate decision: expose the field on the MCP side, or add it
to ``allowed_drops`` with a comment explaining *why* it's intentionally
not exposed (server-managed timestamp, deprecated, routed via a different
sub-payload, etc.).

## Scope (v1)

Covers the five transactional create_* tools the #627 sweep targeted:
- create_purchase_order
- create_sales_order
- create_manufacturing_order
- create_stock_adjustment
- create_stock_transfer

Modify_* tools are not included — the #627 audit found no gaps on the
modify side, so adding them now would be busy-work. Add when a regen
or audit surfaces drift.

Variant-flattened tools (create_product / create_material / create_item)
are also out of v1 scope — they flatten variant fields into the parent
request, which the simple Pairing pattern doesn't model cleanly. Track
as follow-up.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import attrs
import pytest
from katana_mcp.tools.foundation.inventory import CreateStockAdjustmentRequest
from katana_mcp.tools.foundation.manufacturing_orders import (
    CreateManufacturingOrderRequest,
)
from katana_mcp.tools.foundation.purchase_orders import CreatePurchaseOrderRequest
from katana_mcp.tools.foundation.sales_orders import CreateSalesOrderRequest
from katana_mcp.tools.foundation.stock_transfers import CreateStockTransferRequest
from pydantic import BaseModel

from katana_public_api_client.models import (
    CreateManufacturingOrderRequest as ApiCreateMORequest,
    CreatePurchaseOrderRequest as ApiCreatePORequest,
    CreateSalesOrderRequest as ApiCreateSORequest,
    CreateStockAdjustmentRequest as ApiCreateSARequest,
    CreateStockTransferRequest as ApiCreateSTRequest,
)


@dataclass(frozen=True)
class Pairing:
    """One MCP-side pydantic model paired with its API-side attrs counterpart.

    ``renames`` maps API field name → MCP field name when the MCP layer
    intentionally renames a field for ergonomics (e.g. ``order_no`` →
    ``order_number`` for transactional orders). ``allowed_drops`` maps
    API field name → reason; entries here are NOT enforced as MCP-side
    fields, but their omission is documented and reviewable.

    A field on the API model is considered "covered" if any of:
    - it appears verbatim on the MCP model, or
    - the renames map points to an MCP field that exists, or
    - it appears in allowed_drops with a reason.

    Anything else is drift.
    """

    mcp_cls: type[BaseModel]
    api_cls: type
    renames: dict[str, str] = field(default_factory=dict)
    allowed_drops: dict[str, str] = field(default_factory=dict)


PAIRINGS: list[Pairing] = [
    # ---- create_purchase_order ----
    Pairing(
        mcp_cls=CreatePurchaseOrderRequest,
        api_cls=ApiCreatePORequest,
        renames={
            "order_no": "order_number",
            "purchase_order_rows": "items",
            "additional_info": "notes",
        },
    ),
    # ---- create_sales_order ----
    # Skipped fields per the #627 deliberate-omissions table:
    #   status: PENDING is the only sensible initial state; transitions
    #     belong on modify_sales_order. Exposing forces agents to learn
    #     the SO status enum at creation for no real benefit.
    Pairing(
        mcp_cls=CreateSalesOrderRequest,
        api_cls=ApiCreateSORequest,
        renames={
            "order_no": "order_number",
            "sales_order_rows": "items",
            "additional_info": "notes",
        },
        allowed_drops={
            "status": (
                "PENDING-only at creation; status transitions belong on "
                "modify_sales_order. Per #627 deliberate-omissions table."
            ),
        },
    ),
    # ---- create_manufacturing_order ----
    # All three skipped fields are documented in the #627 deliberate-omissions
    # table. Net effect: this tool gets no field additions.
    Pairing(
        mcp_cls=CreateManufacturingOrderRequest,
        api_cls=ApiCreateMORequest,
        allowed_drops={
            "status": ("Only NOT_STARTED is valid at creation; the impl hardcodes it."),
            "actual_quantity": (
                "Computed from production runs — not a creation-time concern."
            ),
            "batch_transactions": (
                "Production-time concern; flows through fulfill_order."
            ),
        },
    ),
    # ---- create_stock_adjustment ----
    Pairing(
        mcp_cls=CreateStockAdjustmentRequest,
        api_cls=ApiCreateSARequest,
        renames={"stock_adjustment_rows": "rows"},
    ),
    # ---- create_stock_transfer ----
    Pairing(
        mcp_cls=CreateStockTransferRequest,
        api_cls=ApiCreateSTRequest,
        renames={
            "stock_transfer_number": "order_no",
            "stock_transfer_rows": "rows",
            "target_location_id": "destination_location_id",
        },
    ),
]


def _attrs_request_field_names(cls: type) -> set[str]:
    """Return the set of *wire* field names on an attrs request class.

    Filters out attrs-internal artifacts:
    - ``additional_properties`` (the open dict sink — not a declared field)
    - any attribute with ``init=False`` (metadata, not part of the request)
    """
    fields = attrs.fields(cls)
    return {f.name for f in fields if f.init and f.name != "additional_properties"}


def _check_pairing(pairing: Pairing) -> tuple[set[str], dict[str, Any]]:
    """Compute the set of API fields with no coverage on the MCP side.

    Returns ``(missing, debug)`` where ``missing`` is the drift set and
    ``debug`` carries the inputs the test prints on failure.
    """
    api_fields = _attrs_request_field_names(pairing.api_cls)
    mcp_fields = set(pairing.mcp_cls.model_fields.keys())

    missing: set[str] = set()
    for api_name in api_fields:
        if api_name in mcp_fields:
            continue
        mapped = pairing.renames.get(api_name)
        if mapped is not None and mapped in mcp_fields:
            continue
        if api_name in pairing.allowed_drops:
            continue
        missing.add(api_name)

    return missing, {
        "api_fields": sorted(api_fields),
        "mcp_fields": sorted(mcp_fields),
        "renames": pairing.renames,
        "allowed_drops": sorted(pairing.allowed_drops.keys()),
    }


@pytest.mark.parametrize(
    "pairing",
    PAIRINGS,
    ids=lambda p: f"{p.mcp_cls.__name__}↔{p.api_cls.__name__}",
)
def test_mcp_request_model_covers_api_fields(pairing: Pairing) -> None:
    """For each pair, every API attrs field must be either exposed on the
    MCP model directly, mapped via ``renames``, or documented in
    ``allowed_drops`` with a reason.

    A failure here means a regen added a field to the generated client
    that the MCP layer hasn't decided about. Either:
    1. Expose it on the MCP model (the usual answer for caller-settable
       business fields), OR
    2. Add it to ``allowed_drops`` with an inline comment explaining why
       (server-managed timestamp, deprecated upstream, routed via a
       different sub-payload, etc.).

    Don't silently rename without updating ``renames`` — the test will
    flag it as missing.
    """
    missing, debug = _check_pairing(pairing)
    assert not missing, (
        f"{pairing.mcp_cls.__name__} is missing API fields from "
        f"{pairing.api_cls.__name__}: {sorted(missing)}\n"
        f"  api_fields:     {debug['api_fields']}\n"
        f"  mcp_fields:     {debug['mcp_fields']}\n"
        f"  renames:        {debug['renames']}\n"
        f"  allowed_drops:  {debug['allowed_drops']}\n"
        f"\n"
        f"Fix one of:\n"
        f"  - Add the field(s) to {pairing.mcp_cls.__name__}, OR\n"
        f"  - Add an entry to allowed_drops with a reason, OR\n"
        f"  - Add a renames entry if the MCP layer renamed the field."
    )


@pytest.mark.parametrize(
    "pairing",
    PAIRINGS,
    ids=lambda p: f"{p.mcp_cls.__name__}↔{p.api_cls.__name__}",
)
def test_renames_actually_resolve_to_mcp_fields(pairing: Pairing) -> None:
    """Sanity: every entry in ``renames`` must point to a field that
    actually exists on the MCP model. Catches stale renames after MCP
    refactors that removed a field — the rename would silently become a
    no-op without this guard.
    """
    mcp_fields = set(pairing.mcp_cls.model_fields.keys())
    stale_renames = {
        api_name: mcp_name
        for api_name, mcp_name in pairing.renames.items()
        if mcp_name not in mcp_fields
    }
    assert not stale_renames, (
        f"{pairing.mcp_cls.__name__}: renames map points to MCP fields "
        f"that no longer exist: {stale_renames}\n"
        f"Available MCP fields: {sorted(mcp_fields)}"
    )


@pytest.mark.parametrize(
    "pairing",
    PAIRINGS,
    ids=lambda p: f"{p.mcp_cls.__name__}↔{p.api_cls.__name__}",
)
def test_allowed_drops_actually_exist_on_api(pairing: Pairing) -> None:
    """Sanity: every entry in ``allowed_drops`` must name a field that
    actually exists on the API attrs model. Otherwise the entry is dead
    weight and likely indicates the API renamed/removed the field —
    which the allowlist should be updated to reflect.
    """
    api_fields = _attrs_request_field_names(pairing.api_cls)
    stale_drops = {
        api_name: reason
        for api_name, reason in pairing.allowed_drops.items()
        if api_name not in api_fields
    }
    assert not stale_drops, (
        f"{pairing.mcp_cls.__name__}: allowed_drops names fields that "
        f"don't exist on {pairing.api_cls.__name__}: "
        f"{sorted(stale_drops.keys())}\n"
        f"Available API fields: {sorted(api_fields)}"
    )
