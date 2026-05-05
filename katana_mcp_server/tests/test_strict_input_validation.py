"""Tests for ``extra="forbid"`` on every MCP-layer input model (#487).

The bug class: pydantic v2 silently drops unknown fields by default. In this
codebase that surfaced as silent partial-success failures across multiple
tools — ``modify_manufacturing_order`` no-op (post-rename of ``confirm`` →
``preview``), ``modify_item`` configs silently dropped (#503),
``receive_purchase_order`` per-item ``received_date`` silently dropped (#505).

This module guards against the bug class in two ways:

1. **Introspection test** — walks every input-shape Pydantic class under
   ``katana_mcp.tools.foundation.*`` and asserts ``model_config["extra"] ==
   "forbid"``. Catches the next sub-payload added without the config.

2. **Behavior tests** — concrete typo cases that mirror the original bug
   reports, asserting the resulting ``ValidationError`` names the
   unknown field so callers can fix the call.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Any

import pytest
from katana_mcp.tools import foundation
from katana_mcp.tools._modification import ConfirmableRequest
from pydantic import BaseModel, ValidationError

# Class-name suffixes that mark a model as "input shape". Output suffixes are
# checked first — a class ending in ``Info``/``Response``/``Summary``/etc. is
# never considered input even if it also matches an input suffix (e.g.
# ``StockAdjustmentRowInfo`` ends with ``Info``, not ``Row``).
_INPUT_SUFFIXES = (
    "Request",
    "Patch",
    "Add",
    "Update",
    "Input",
    "Item",
    "Params",
    "Row",
    "Address",
)
_OUTPUT_SUFFIXES = ("Response", "Info", "Summary", "Detail", "Stats")

# Class names exempt from the ``extra="forbid"`` requirement. Add with a
# brief justification — the goal is to keep this list tiny.
_EXEMPT_CLASSES: frozenset[str] = frozenset()


def _is_input_class_name(name: str) -> bool:
    if any(name.endswith(suf) for suf in _OUTPUT_SUFFIXES):
        return False
    return any(name.endswith(suf) for suf in _INPUT_SUFFIXES)


def _all_foundation_input_classes() -> list[type[BaseModel]]:
    """Discover every input-shape ``BaseModel`` subclass across all modules
    under ``katana_mcp.tools.foundation``."""
    collected: list[type[BaseModel]] = []
    for module_info in pkgutil.iter_modules(foundation.__path__):
        if module_info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{foundation.__name__}.{module_info.name}")
        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if not issubclass(obj, BaseModel) or obj is BaseModel:
                continue
            if obj.__module__ != module.__name__:
                continue  # imported from elsewhere
            if obj.__name__ in _EXEMPT_CLASSES:
                continue
            if not _is_input_class_name(obj.__name__):
                continue
            collected.append(obj)
    return collected


def test_every_foundation_input_model_forbids_extra() -> None:
    """Every input-shape Pydantic model in ``foundation/`` must reject
    unknown fields. Adding a new patch/sub-payload model without
    ``extra="forbid"`` will fail this test — that's the point."""
    classes = _all_foundation_input_classes()
    assert classes, "discovered zero input classes — exploration logic broke"

    missing: list[str] = []
    for cls in classes:
        if cls.model_config.get("extra") != "forbid":
            missing.append(f"{cls.__module__}.{cls.__name__}")

    assert not missing, (
        f"{len(missing)} input model(s) missing extra='forbid' — add "
        f"`model_config = ConfigDict(extra='forbid')` to each:\n  "
        + "\n  ".join(missing)
    )


def test_confirmable_request_forbids_extra() -> None:
    """The base class for every ``Modify*Request`` and ``Delete*Request``
    inherits ``extra="forbid"`` so dispatcher-level typos are caught when
    callers go through direct Python (tests, internal ``_impl`` calls)."""
    assert ConfirmableRequest.model_config.get("extra") == "forbid"


# ============================================================================
# Behavior tests — one per foundation file's flagship sub-payload, plus the
# original bug-report cases. Each asserts ValidationError names the unknown
# field so the caller can fix the call.
# ============================================================================


def _assert_forbids(
    model_cls: type[BaseModel], known_kwargs: dict[str, Any], unknown_field: str
) -> None:
    """Construct the model with one extra field; assert ValidationError
    mentions the extra field name."""
    with pytest.raises(ValidationError) as exc:
        model_cls(**known_kwargs, **{unknown_field: 1})
    assert unknown_field in str(exc.value), (
        f"ValidationError for {model_cls.__name__} should mention "
        f"unknown field {unknown_field!r}; got: {exc.value!s}"
    )


def test_po_row_add_rejects_unknown_field() -> None:
    from katana_mcp.tools.foundation.purchase_orders import PORowAdd

    _assert_forbids(
        PORowAdd,
        known_kwargs={"variant_id": 1, "quantity": 1, "price_per_unit": 1.0},
        unknown_field="landed_cost",
    )


def test_so_header_patch_rejects_unknown_field() -> None:
    from katana_mcp.tools.foundation.sales_orders import SOHeaderPatch

    _assert_forbids(SOHeaderPatch, known_kwargs={}, unknown_field="unknown_field")


def test_mo_recipe_row_update_rejects_unknown_field() -> None:
    from katana_mcp.tools.foundation.manufacturing_orders import MORecipeRowUpdate

    _assert_forbids(MORecipeRowUpdate, known_kwargs={"id": 1}, unknown_field="bogus")


def test_item_header_patch_rejects_unknown_field() -> None:
    from katana_mcp.tools.foundation.items import ItemHeaderPatch

    _assert_forbids(ItemHeaderPatch, known_kwargs={}, unknown_field="config_attributes")


def test_stock_transfer_header_patch_rejects_unknown_field() -> None:
    from katana_mcp.tools.foundation.stock_transfers import StockTransferHeaderPatch

    _assert_forbids(
        StockTransferHeaderPatch, known_kwargs={}, unknown_field="ghost_field"
    )


def test_receive_item_request_rejects_received_date_505() -> None:
    """#505: the original bug — ``received_date`` silently dropped on
    ``ReceiveItemRequest``. Now surfaces loudly so the caller knows the
    field isn't supported and to use ``modify_purchase_order`` for back-dating."""
    from katana_mcp.tools.foundation.purchase_orders import ReceiveItemRequest

    _assert_forbids(
        ReceiveItemRequest,
        known_kwargs={"purchase_order_row_id": 1, "quantity": 1},
        unknown_field="received_date",
    )


def test_modify_po_request_rejects_dispatcher_typo() -> None:
    """``ConfirmableRequest`` base — typos like ``previw=False`` (instead of
    ``preview``) on direct Python callers must be loud, not silent. (MCP
    protocol traffic is already protected by FastMCP's TypeAdapter against
    the function signature.)"""
    from katana_mcp.tools.foundation.purchase_orders import ModifyPurchaseOrderRequest

    _assert_forbids(
        ModifyPurchaseOrderRequest, known_kwargs={"id": 1}, unknown_field="previw"
    )
