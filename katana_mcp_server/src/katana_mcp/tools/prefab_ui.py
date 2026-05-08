"""Prefab UI builders for Katana MCP Server tool responses.

Provides reusable Prefab component builders that produce rich interactive UIs
for MCP Apps-capable hosts (Claude Desktop, etc.) via the
``ui://prefab/renderer.html`` resource auto-registered by fastmcp 3.x.

Usage::

    from katana_mcp.tools.prefab_ui import (
        build_search_results_ui,
        build_item_detail_ui,
        build_order_preview_ui,
        build_order_created_ui,
    )

    # In a tool's *_to_tool_result function:
    items_dicts = [item.model_dump() for item in response.items]
    app = build_search_results_ui(items_dicts, query, response.total_count)
    return make_tool_result(response, ui=app)
"""

from __future__ import annotations

from typing import Any, Literal

from prefab_ui.actions import Action, SetState, ShowToast
from prefab_ui.actions.mcp import CallTool, SendMessage, UpdateContext
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    H3,
    Alert,
    AlertDescription,
    AlertTitle,
    Badge,
    Button,
    Card,
    CardContent,
    CardFooter,
    CardHeader,
    CardTitle,
    Column,
    DataTable,
    DataTableColumn,
    Metric,
    Muted,
    Row,
    Separator,
    Text,
)
from prefab_ui.components.control_flow import Elif, Else, ForEach, If
from prefab_ui.components.slot import Slot
from prefab_ui.rx import RESULT, Rx
from pydantic import BaseModel

from katana_mcp.tools.tool_result_utils import BLOCK_WARNING_PREFIX


def _split_warnings(
    warnings: list[str] | None,
) -> tuple[list[str], list[str]]:
    """Split a warnings list into (block_warnings, regular_warnings).

    Block warnings have the ``BLOCK:`` prefix stripped so they render as plain
    user-facing text. Their presence tells the caller to omit the Confirm
    button. Regular warnings render as informational badges only.
    """
    if not warnings:
        return [], []
    blocks: list[str] = []
    regulars: list[str] = []
    for w in warnings:
        if w.startswith(BLOCK_WARNING_PREFIX):
            blocks.append(w[len(BLOCK_WARNING_PREFIX) :].lstrip())
        else:
            regulars.append(w)
    return blocks, regulars


# Coaching text appended to every preview-mode write tool's description so
# the agent (1) does not re-narrate or ask for chat-confirmation after a
# preview returns (closes #544), and (2) knows to re-issue the call when it
# sees an ``Apply: call ...`` SendMessage from a Confirm-button click. The
# rationale lives in ADR-0015.
PREVIEW_APPLY_COACHING = (
    "Preview→apply: when ``preview=True`` (default), returns a Prefab card "
    "with Confirm/Cancel buttons. Do NOT re-narrate the card or ask for "
    "confirmation in chat — the buttons handle that. End your turn after "
    "the preview response.\n\n"
    "If you receive a chat message starting with ``Apply: call <tool>(...)`` "
    "or ``Cancel: do not apply ...``, that is a button click from a previous "
    "preview. For Apply, re-issue the tool call exactly as written. For "
    "Cancel, acknowledge briefly without re-issuing."
)


# Coaching text for tools using the direct-apply rail (Confirm button fires
# ``tools/call`` directly + iframe pushes the structured result back via
# ``ui/update-model-context``). The agent does not re-issue the call — it
# receives the apply result automatically on its next turn. See
# ``docs/adr/0016-direct-apply-confirm-button-rail.md`` (forthcoming).
PREVIEW_APPLY_DIRECT_COACHING = (
    "Preview→apply: when ``preview=True`` (default) AND the host renders "
    "MCP Apps iframes (Claude Desktop, Claude.ai, Cowork, etc.), returns a "
    "Prefab card with Confirm/Cancel buttons. Do NOT re-narrate the card or "
    "ask for confirmation in chat — the buttons handle that. End your turn "
    "after the preview response.\n\n"
    "When the user clicks Confirm in the iframe, the iframe fires the apply "
    "call directly and morphs in place to a result card. The structured "
    "apply response (id, status, etc.) arrives in your context on your next "
    "turn via ``ui/update-model-context``. Treat it as you would any "
    "tool-call result — acknowledge completion, suggest next steps. Do NOT "
    "re-issue the call after the iframe already applied.\n\n"
    "Non-iframe-host fallback: if the host does not render Prefab cards "
    "(no iframe was shown to the user), there are no buttons. Ask the user "
    "for confirmation in chat, then re-issue with ``preview=False`` "
    "yourself.\n\n"
    "If you receive a chat message starting with ``Cancel: do not apply ...``, "
    "the user opted out — acknowledge briefly without re-issuing."
)


def with_preview_coaching(fn: Any, *, direct: bool = False) -> str:
    """Build a FastMCP tool description by appending preview→apply coaching
    to the function's docstring.

    Two coaching variants:

    - ``direct=False`` (default): tools using the SendMessage rail. Confirm
      fires a ``Apply: call <tool>(...)`` chat message; agent re-issues.
    - ``direct=True``: tools using the direct-apply rail. Confirm fires
      ``tools/call`` directly and pushes the result via
      ``ui/update-model-context``; agent does not re-issue.

    Most callers should use :func:`register_preview_tool` rather than
    calling this directly.
    """
    coaching = PREVIEW_APPLY_DIRECT_COACHING if direct else PREVIEW_APPLY_COACHING
    base = (fn.__doc__ or "").strip()
    return f"{base}\n\n{coaching}" if base else coaching


def register_preview_tool(
    mcp: Any,
    fn: Any,
    *,
    tags: set[str],
    annotations: Any,
    meta: Any = None,
    direct: bool = False,
) -> None:
    """Register a preview-mode write tool with standard coaching applied.

    Set ``direct=True`` for tools whose preview UI uses the direct-apply
    rail (Confirm button fires ``tools/call`` directly and pushes the
    structured result back via ``ui/update-model-context``). Default
    ``direct=False`` uses the SendMessage rail (Confirm fires a chat
    ``Apply: call ...`` for the agent to re-issue).
    """
    mcp.tool(
        description=with_preview_coaching(fn, direct=direct),
        tags=tags,
        annotations=annotations,
        meta=meta,
    )(fn)


def _build_apply_message(tool_name: str, args: dict[str, Any]) -> str:
    """Format the SendMessage text the Confirm button emits to prompt the
    agent to re-issue the apply tool call.

    Shape (uniform across all preview-mode write tools)::

        Apply: call <tool_name>(<key>=<value>, ..., preview=False)

    The message is human-readable and machine-parseable: the agent's tool
    description coaches it to recognize the ``Apply:`` prefix and re-invoke
    ``<tool_name>`` with the inlined args verbatim. ``preview=False`` is
    placed last regardless of where ``preview`` appears in ``args.items()``
    iteration order — for ``ConfirmableRequest`` subclasses the base-class
    ``preview`` field can appear in the middle, but the agent should read
    a stable trailing ``, preview=False)``.

    ``args`` comes from ``request.model_dump(mode="json")``, so values are
    already JSON primitives (str, None, bool, int/float, list, dict) — we
    can use built-in ``repr`` for byte-identical Python-source rendering.
    """
    body = ", ".join(
        f"{key}={value!r}" for key, value in args.items() if key != "preview"
    )
    suffix = "preview=False"
    inner = f"{body}, {suffix}" if body else suffix
    return f"Apply: call {tool_name}({inner})"


def _build_apply_action(
    confirm_tool: str | None,
    confirm_request: BaseModel | None,
) -> list[Action] | None:
    """Construct the Confirm-button click action, or ``None`` when both
    inputs are ``None``.

    The action does **not** call the apply tool directly. By MCP spec, an
    iframe-initiated ``tools/call`` returns its result to the iframe, not to
    the agent's context — so the agent would never see the structured apply
    response. Instead, the click marks the preview card as ``pending`` and
    sends a ``SendMessage`` instructing the agent to re-issue the call. The
    agent then makes the real tool call through its own tool-calling loop
    and gets the full structured response back.

    See ``docs/adr/0015-confirmation-pattern-for-write-tools.md`` for the
    architectural rationale.

    ``confirm_tool`` and ``confirm_request`` must be both set or both
    ``None`` (the latter for builders that render their non-preview
    branch — no Confirm button to wire).
    """
    if confirm_tool is None and confirm_request is None:
        return None
    if confirm_tool is None or confirm_request is None:
        raise ValueError(
            "confirm_tool and confirm_request must be set together (or both None)"
        )
    args = confirm_request.model_dump(mode="json")
    if "preview" not in args:
        raise ValueError(
            f"_build_apply_action requires a request model with a "
            f"`preview` field; {type(confirm_request).__name__} has none. "
            f"Without that field the SendMessage would tell the agent to "
            f"re-issue {confirm_tool} with an unrecognized preview=False "
            f"argument, failing validation downstream."
        )
    args["preview"] = False
    return [
        SetState("pending", True),
        SendMessage(_build_apply_message(confirm_tool, args)),
    ]


def _build_apply_action_direct(
    confirm_tool: str | None,
    confirm_request: BaseModel | None,
    *,
    extra_on_success: list[Action] | None = None,
) -> list[Action] | None:
    """Construct the direct-apply Confirm-button click action chain.

    The chain is ``[SetState(pending, True), CallTool(...)]``. Setting
    ``pending=True`` synchronously before the call fires is the spam guard:
    the buttons bind ``disabled=Rx("pending") | ...`` so a second click
    while the call is in flight is dropped (no duplicate POs). The
    ``on_success`` / ``on_error`` chains clear ``pending`` and flip
    ``applied`` / ``error`` for the in-place morph.

    On success the iframe pushes the structured result back to the agent's
    model context via ``ui/update-model-context`` (MCP Apps spec,
    SEP-1865, 2026-01-26). The agent sees the result on its next turn —
    no re-issue needed.

    On error the iframe shows the error inline and pushes the error
    reason into model context so the agent can react on its next turn.

    The ``UpdateContext.content`` field (text channel) is the spec-correct
    one for agent-visible context: per the MCP Apps spec, ``content``
    reaches the model; ``structuredContent`` is for UI rendering and is
    not guaranteed in model context.

    See ``docs/adr/0016-direct-apply-confirm-button-rail.md`` (forthcoming)
    for the architectural rationale; supersedes ADR-0015 for tools that
    opt into this rail.

    ``confirm_tool`` and ``confirm_request`` must be both set or both
    ``None`` (the latter for builders that render their non-preview branch).
    """
    if confirm_tool is None and confirm_request is None:
        return None
    if confirm_tool is None or confirm_request is None:
        raise ValueError(
            "confirm_tool and confirm_request must be set together (or both None)"
        )
    args = confirm_request.model_dump(mode="json")
    if "preview" not in args:
        raise ValueError(
            f"_build_apply_action_direct requires a request model with a "
            f"`preview` field; {type(confirm_request).__name__} has none."
        )
    args["preview"] = False
    # The on_success chain runs the caller's extras BEFORE the generic
    # flags so a builder that pushes RESULT.actions into a state slot (e.g.
    # the modification card binding ``state.plan_actions`` for live-tick row
    # updates) sees its row data land before the iframe morphs to its
    # ``applied=True`` rendering.
    on_success: list[Action] = [
        *(extra_on_success or []),
        SetState("pending", False),
        SetState("applied", True),
        SetState("result", RESULT),
        UpdateContext(content=RESULT),
    ]
    return [
        # Click guard — disables the button immediately so a double-click
        # in the iframe can't fire two applies (which would create
        # duplicate POs etc.). Cleared in on_success/on_error.
        SetState("pending", True),
        CallTool(
            tool=confirm_tool,
            arguments=args,
            on_success=on_success,
            on_error=[
                SetState("pending", False),
                SetState("error", "{{ $error }}"),
                ShowToast("{{ $error }}", variant="error"),
                UpdateContext(content="Apply failed: {{ $error }}"),
            ],
        ),
    ]


def _build_cancel_action(operation_label: str) -> list[Action]:
    """Construct the Cancel-button click action.

    Marks the preview card as ``cancelled`` (so the buttons gray out + a
    "Cancelled" pill appears) and sends a ``SendMessage`` so the agent
    knows the user opted out. The agent's tool description coaches it to
    acknowledge briefly and move on without re-issuing.

    ``operation_label`` is a human-readable phrase like ``"the fulfillment"``
    or ``"that preview"`` — embedded in the SendMessage text so the agent
    has enough context to acknowledge specifically.
    """
    return [
        SetState("cancelled", True),
        SendMessage(f"Cancel: do not apply {operation_label}."),
    ]


def _render_apply_button_row(
    *,
    confirm_label: str,
    apply_action: list[Action] | None,
    cancel_action: list[Action],
    disabled: bool = False,
    direct_apply: bool = False,
) -> None:
    """Render the preview-card button row with state-aware visuals.

    States driven by iframe state:

    - **Default** — Confirm + Cancel buttons enabled.
    - **Pending…** — pill rendered, both buttons disabled. Set on click for
      both rails: SendMessage rail uses it as the re-issue handoff signal;
      direct-apply rail uses it as the in-flight click guard so a
      double-click cannot fire two applies. Cleared in on_success /
      on_error for direct rail; persists for SendMessage rail (the agent
      re-issue replaces the card).
    - **Applied** — pill rendered, both buttons disabled. Direct-apply rail
      only (``direct_apply=True``); apply succeeded and the iframe morphed.
    - **Error** — pill rendered, both buttons disabled. Direct-apply rail
      only; apply failed. The error reason is in iframe state and was
      pushed to the agent via ``ui/update-model-context``.
    - **Cancelled** — pill rendered, both buttons disabled, after Cancel
      click.

    ``disabled=True`` is the block-warning fallback: only the Cancel button
    is offered (no Confirm). The Cancel button still binds
    ``disabled=Rx("cancelled")`` and renders a "Cancelled" pill on click,
    matching the spam-protection contract of the non-block-warning rail.
    """
    if disabled or apply_action is None:
        with Row(gap=2):
            with If("cancelled"):
                Badge(label="Cancelled", variant="secondary")
            Button(
                label="Cancel",
                variant="outline",
                on_click=cancel_action,
                disabled=Rx("cancelled"),
            )
        return

    if direct_apply:
        # `pending` is the in-flight guard — set on click before CallTool
        # fires, cleared in on_success/on_error. Including it in `locked`
        # is what prevents double-click from firing two applies.
        locked = Rx("pending") | Rx("applied") | Rx("error") | Rx("cancelled")
    else:
        locked = Rx("pending") | Rx("cancelled")
    with Row(gap=2):
        if direct_apply:
            with If("pending"):
                Badge(label="Applying…", variant="secondary")
            with Elif("applied"):
                Badge(label="Applied", variant="default")
            with Elif("error"):
                Badge(label="Error", variant="destructive")
            with Elif("cancelled"):
                Badge(label="Cancelled", variant="secondary")
        else:
            with If("pending"):
                Badge(label="Pending…", variant="secondary")
            with Elif("cancelled"):
                Badge(label="Cancelled", variant="secondary")
        Button(
            label=confirm_label,
            variant="default",
            on_click=apply_action,
            disabled=locked,
        )
        Button(
            label="Cancel",
            variant="outline",
            on_click=cancel_action,
            disabled=locked,
        )


# ============================================================================
# Search & Browse UIs
# ============================================================================


def build_search_results_ui(
    items: list[dict[str, Any]],
    query: str,
    total_count: int,
) -> PrefabApp:
    """Build an interactive search results table with drill-down.

    Features:
    - Sortable, searchable, paginated DataTable
    - Row-click fires CallTool to get_variant_details, renders in Slot
    - Summary badges for query and count

    When ``total_count == 0``, drops the DataTable / drill-down Slot /
    "Check inventory" button — they all reference nonexistent results — and
    renders a friendly hint suggesting partial-SKU / name fallbacks. Closes
    #470.
    """
    with (
        PrefabApp(
            state={"items": items, "detail": None},
            css_class="p-4",
        ) as app,
        Column(gap=4),
    ):
        with Row(gap=2):
            H3(content="Search Results")
            Badge(label=f"Query: {query}", variant="outline")
            Badge(label=f"{total_count} items", variant="secondary")

        if total_count == 0:
            Muted(
                content=(
                    f'No items match "{query}". Try a partial SKU, variant '
                    "name, or parent product/material name — search uses "
                    "FTS5 with fuzzy fallback."
                )
            )
            return app

        DataTable(
            columns=[
                DataTableColumn(key="sku", header="SKU", sortable=True),
                DataTableColumn(key="name", header="Name", sortable=True),
                DataTableColumn(
                    key="is_sellable",
                    header="Sellable",
                    sortable=True,
                ),
                DataTableColumn(
                    key="is_archived",
                    header="Archived",
                    sortable=True,
                ),
            ],
            rows="{{ items }}",
            search=True,
            paginated=True,
            pageSize=20,
            # NOTE: ``{{ sku }}`` and ``{{ $error }}`` here are *per-row /
            # event-context* bindings provided by the DataTable component
            # itself, NOT the iframe-state substitution that broke in #491.
            # The DataTable renderer expands these client-side from the
            # clicked row's data and the action's error payload, so they
            # do not depend on the host-side Mustache-from-state mechanism
            # that silently dropped args. Reliability is owned by the
            # DataTable component; verification is tracked in #494.
            onRowClick=CallTool(
                "get_variant_details",
                arguments={"sku": "{{ sku }}"},
                on_success=SetState("detail", RESULT),
                on_error=ShowToast("{{ $error }}", variant="error"),
            ),
        )

        with Slot(name="detail"):
            Muted(content="Click a row to see variant details")

        with Row(gap=2):
            Button(
                label="Check inventory for search results",
                variant="outline",
                on_click=SendMessage(
                    "Check inventory levels for the items in my search results"
                ),
            )
    return app


def _variant_header_section(variant: dict[str, Any]) -> None:
    """Render variant card header: title, badges, parent, config-attribute pills."""
    with Row(gap=2):
        CardTitle(content=variant.get("name", "Unknown"))
        Badge(label=variant.get("sku", ""), variant="outline")
        if variant.get("type"):
            Badge(label=variant["type"], variant="secondary")
        if variant.get("is_batch_tracked"):
            Badge(label="Batch tracked", variant="secondary")
    parent_name = variant.get("product_or_material_name")
    if parent_name:
        Muted(content=f"Part of: {parent_name}")
    # Config-attribute pills (size / color / volume) inline so the
    # variant's distinguishing axes are visible without scrolling.
    config_attrs = variant.get("config_attributes") or []
    if config_attrs:
        with Row(gap=2):
            for attr in config_attrs:
                if not isinstance(attr, dict):
                    continue
                label = attr.get("config_name") or ""
                value = attr.get("config_value") or ""
                if label and value:
                    Badge(label=f"{label}: {value}", variant="outline")


def _variant_supplier_line(variant: dict[str, Any]) -> None:
    """Render the default-supplier text row when name and/or id is set."""
    name = variant.get("default_supplier_name")
    sid = variant.get("default_supplier_id")
    if name and sid:
        Text(content=f"Default Supplier: {name} ({sid})")
    elif name:
        Text(content=f"Default Supplier: {name}")
    elif sid:
        Text(content=f"Default Supplier ID: {sid}")


def _variant_barcode_line(variant: dict[str, Any]) -> None:
    """Render the barcode text row when at least one barcode is set."""
    parts = []
    if variant.get("internal_barcode"):
        parts.append(f"internal={variant['internal_barcode']}")
    if variant.get("registered_barcode"):
        parts.append(f"registered={variant['registered_barcode']}")
    if parts:
        Text(content=f"Barcodes: {', '.join(parts)}")


def _variant_id_line(variant: dict[str, Any]) -> None:
    """IDs deprioritized to a single Muted row at the bottom — they're
    useful for follow-up tool calls but not the primary signal a human
    reader needs.
    """
    id_parts = [f"variant_id={variant.get('id', 'N/A')}"]
    if variant.get("product_id"):
        id_parts.append(f"product_id={variant['product_id']}")
    if variant.get("material_id"):
        id_parts.append(f"material_id={variant['material_id']}")
    Muted(content=" · ".join(id_parts))


def _variant_reference_section(variant: dict[str, Any]) -> None:
    """Render the reference data block (UoM, supplier, lead time, codes, IDs)."""
    if variant.get("uom"):
        Text(content=f"UoM: {variant['uom']}")
    _variant_supplier_line(variant)
    if variant.get("lead_time") is not None:
        Text(content=f"Lead Time: {variant['lead_time']} days")
    if variant.get("minimum_order_quantity") is not None:
        Text(content=f"Min Order Qty: {variant['minimum_order_quantity']}")
    _variant_barcode_line(variant)
    if variant.get("supplier_item_codes"):
        Muted(content="Supplier Codes:")
        with ForEach("variant.supplier_item_codes"):
            Text(content="{{ $item }}")
    _variant_id_line(variant)


def _variant_footer_section(variant: dict[str, Any]) -> None:
    """Render footer action buttons."""
    sku = variant.get("sku", "")
    if variant.get("katana_url"):
        Button(
            label="View in Katana",
            variant="outline",
            on_click=SendMessage(f"Open the Katana URL: {variant['katana_url']}"),
        )
    Button(
        label="Check Inventory",
        variant="outline",
        on_click=SendMessage(f"Check inventory for SKU {sku}"),
    )
    Button(
        label="Create Purchase Order",
        variant="outline",
        on_click=SendMessage(f"Draft a purchase order for SKU {sku}"),
    )
    if variant.get("type") == "material" and variant.get("id"):
        Button(
            label="List MOs Using This",
            variant="outline",
            on_click=SendMessage(
                f"List manufacturing orders that use variant_id {variant['id']}"
            ),
        )


def build_variant_details_ui(
    variant: dict[str, Any],
) -> PrefabApp:
    """Build a detail card for a variant.

    Designed for the "should I order more / where is this used / how is
    it tracked" decisions. Surfaces the facts an inventory-aware agent
    needs first (UoM, default supplier, batch tracking, config
    attributes), with raw IDs deprioritized to a footer-style row. See
    #538 for the design rationale.
    """
    uom = variant.get("uom")

    def _price_display(p: float | None) -> str:
        if p is None:
            return "N/A"
        suffix = f" / {uom}" if uom and uom not in ("pcs", "ea") else ""
        return f"${p:,.2f}{suffix}"

    with PrefabApp(state={"variant": variant}, css_class="p-4") as app, Card():
        with CardHeader(), Column(gap=1):
            _variant_header_section(variant)

        with CardContent(), Column(gap=3):
            with Row(gap=4):
                Metric(
                    label="Sales Price",
                    value=_price_display(variant.get("sales_price")),
                )
                Metric(
                    label="Purchase Price",
                    value=_price_display(variant.get("purchase_price")),
                )
            Separator()
            _variant_reference_section(variant)

        with CardFooter(), Row(gap=2):
            _variant_footer_section(variant)
    return app


def build_item_detail_ui(
    item: dict[str, Any],
) -> PrefabApp:
    """Build a detail card for an item (product/material/service)."""
    with PrefabApp(state={"item": item}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=item.get("name", "Unknown"))
            Badge(label=item.get("type", ""), variant="secondary")

        with CardContent(), Column(gap=2):
            Text(content=f"ID: {item.get('id', 'N/A')}")
            if item.get("uom"):
                Text(content=f"Unit of Measure: {item['uom']}")
            if item.get("category_name"):
                Text(content=f"Category: {item['category_name']}")

            with Row(gap=2):
                if item.get("is_sellable") is not None:
                    Badge(
                        label="Sellable" if item["is_sellable"] else "Not Sellable",
                        variant="default" if item["is_sellable"] else "secondary",
                    )
                if item.get("is_producible") is not None:
                    Badge(
                        label="Producible"
                        if item["is_producible"]
                        else "Not Producible",
                        variant="default" if item["is_producible"] else "secondary",
                    )
                if item.get("is_archived"):
                    Badge(label="Archived", variant="secondary")

        with CardFooter(), Row(gap=2):
            if item.get("sku"):
                Button(
                    label="Get Variant Details",
                    variant="outline",
                    on_click=SendMessage(f"Get variant details for SKU {item['sku']}"),
                )
                Button(
                    label="Check Inventory",
                    variant="outline",
                    on_click=SendMessage(f"Check inventory for SKU {item['sku']}"),
                )
    return app


# ============================================================================
# Inventory UIs
# ============================================================================


def build_inventory_check_ui(
    stock: dict[str, Any],
) -> PrefabApp:
    """Build an inventory check card."""
    by_location = stock.get("by_location") or []
    with PrefabApp(state={"stock": stock}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=stock.get("product_name", "Unknown"))
            Badge(label=stock.get("sku", ""), variant="outline")
            # When stock is split across multiple warehouses, surface the
            # count up front so the agent knows to look at the breakdown
            # below — the headline number alone hides where the stock is.
            if len(by_location) > 1:
                Badge(
                    label=f"{len(by_location)} locations",
                    variant="secondary",
                )

        with CardContent(), Column(gap=3):
            with Row(gap=4):
                Metric(label="In Stock", value=str(stock.get("in_stock", 0)))
                Metric(label="Available", value=str(stock.get("available_stock", 0)))
                Metric(label="Committed", value=str(stock.get("committed", 0)))
                Metric(label="Expected", value=str(stock.get("expected", 0)))

            # Per-location breakdown — only when stock is actually split
            # across more than one warehouse (single-location case stays
            # quiet). Resolves #529's headline workflow ("where IS the
            # demo bike?") in the single-SKU card path that
            # check_inventory's most-common usage hits.
            if len(by_location) > 1:
                Separator()
                Muted(content="By location:")
                DataTable(
                    columns=[
                        DataTableColumn(key="location_name", header="Location"),
                        DataTableColumn(key="location_id", header="ID"),
                        DataTableColumn(key="in_stock", header="In Stock"),
                        DataTableColumn(key="committed", header="Committed"),
                        DataTableColumn(key="available", header="Available"),
                        DataTableColumn(key="expected", header="Expected"),
                    ],
                    rows="{{ stock.by_location }}",
                )

        with CardFooter(), Row(gap=2):
            Button(
                label="Reorder",
                variant="outline",
                on_click=SendMessage(
                    f"Draft a purchase order to reorder SKU {stock.get('sku', '')}"
                ),
            )
            Button(
                label="View Low Stock",
                variant="outline",
                on_click=SendMessage("List all items with low stock levels"),
            )
    return app


def build_low_stock_ui(
    items: list[dict[str, Any]],
    threshold: int,
    total_count: int,
) -> PrefabApp:
    """Build a low stock report with table and reorder action.

    When ``total_count == 0``, drops the DataTable and "Create Restock
    Orders" button — they reference nonexistent items — and renders a
    friendly "all clear" hint instead. Bundled with the #470 search empty-
    state fix because the pattern is identical.
    """
    with (
        PrefabApp(
            state={"items": items},
            css_class="p-4",
        ) as app,
        Column(gap=4),
    ):
        with Row(gap=2):
            H3(content="Low Stock Report")
            Badge(label=f"Threshold: {threshold}", variant="outline")
            Badge(
                label=f"{total_count} items",
                variant="destructive" if total_count > 0 else "secondary",
            )

        if total_count == 0:
            Muted(
                content=(
                    f"No items below the threshold of {threshold}. "
                    "Inventory levels are healthy."
                )
            )
            return app

        DataTable(
            columns=[
                DataTableColumn(key="sku", header="SKU", sortable=True),
                DataTableColumn(key="product_name", header="Product", sortable=True),
                DataTableColumn(
                    key="current_stock",
                    header="Current Stock",
                    sortable=True,
                    align="right",
                ),
                DataTableColumn(
                    key="threshold",
                    header="Threshold",
                    align="right",
                ),
            ],
            rows="{{ items }}",
            search=True,
            paginated=True,
        )

        Button(
            label="Create Restock Orders",
            variant="default",
            on_click=SendMessage(
                "Create purchase orders to restock all low-stock items"
            ),
        )
    return app


# ============================================================================
# Stock Adjustment UIs (Create / Update / Delete)
# ============================================================================


_STOCK_ADJUSTMENT_ROW_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="sku", header="SKU"),
    DataTableColumn(key="display_name", header="Item"),
    DataTableColumn(key="quantity_label", header="Qty Change", align="right"),
    DataTableColumn(key="cost_label", header="Cost / unit", align="right"),
]

_STOCK_ADJUSTMENT_FIELD_DIFF_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="field", header="Field"),
    DataTableColumn(key="new_value", header="New Value"),
]


def _format_qty_change(qty: float) -> str:
    """Format a quantity change with leading sign (e.g., ``+1.0``, ``-3.5``)."""
    return f"{qty:+.1f}"


def _format_cost(cost: float | int | None) -> str:
    """Format a per-unit cost; ``—`` when omitted."""
    if cost is None:
        return "—"
    return f"{cost:.2f}"


# Initial state slots written by the direct-apply rail's Confirm/Cancel
# action chains. Builders that opt into the rail seed these to ``False`` /
# ``None`` so the iframe's If/Elif blocks have something to bind to before
# the first click. ``SetState`` mutations from
# ``_build_apply_action_direct`` / ``_build_cancel_action`` flip them.
_DIRECT_APPLY_STATE_INIT: dict[str, Any] = {
    "pending": False,
    "cancelled": False,
    "applied": False,
    "error": None,
}


def _stock_adjustment_rows_for_table(
    rows: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Project StockAdjustmentRowSummary dicts onto the DataTable row shape.

    Trusts the upstream pydantic model's type guarantees — the dict comes
    from ``StockAdjustmentResponse.model_dump()`` so ``sku`` /
    ``display_name`` / ``quantity`` are already correctly typed.
    """
    return [
        {
            "sku": r["sku"],
            "display_name": r["display_name"],
            "quantity_label": _format_qty_change(r["quantity"]),
            "cost_label": _format_cost(r.get("cost_per_unit")),
        }
        for r in (rows or [])
    ]


def build_stock_adjustment_create_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the create-stock-adjustment preview card with direct-apply rail.

    Used for both the ``preview=True`` branch (Confirm + Cancel buttons,
    direct-apply morph) and the ``preview=False`` branch (no buttons,
    "View in Katana" link). The same builder handles both via the
    ``is_preview`` flag — symmetric with how the modification card
    pair is structured.
    """
    is_preview = bool(response.get("is_preview"))
    rows = _stock_adjustment_rows_for_table(response.get("rows"))
    state: dict[str, Any] = {"plan_rows": rows}
    apply_action: list[Action] | None = None
    cancel_action: list[Action] | None = None
    if is_preview:
        state.update(_DIRECT_APPLY_STATE_INIT)
        apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
        cancel_action = _build_cancel_action("the stock adjustment")

    location_id = response.get("location_id")
    adj_id = response.get("id")
    reason = response.get("reason")

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content="Stock Adjustment")
            if adj_id is not None:
                Badge(label=f"#{adj_id}", variant="outline")
            if location_id is not None:
                Badge(label=f"Location {location_id}", variant="outline")
            Badge(
                label="PREVIEW" if is_preview else "APPLIED",
                variant="secondary" if is_preview else "default",
            )

        with CardContent(), Column(gap=3):
            if response.get("message"):
                Text(content=response["message"])
            if reason:
                Muted(content=f"Reason: {reason}")

            if rows:
                DataTable(
                    columns=_STOCK_ADJUSTMENT_ROW_COLUMNS,
                    rows="{{ plan_rows }}",
                )

            if is_preview:
                with If("error"):
                    Separator()
                    with Alert(variant="destructive", icon="circle-alert"):
                        AlertTitle(content="Apply failed")
                        AlertDescription(content="{{ error }}")

        with CardFooter(), Row(gap=2):
            if apply_action is not None and cancel_action is not None:
                with If("applied"):
                    Muted(content="Stock adjustment created.")
                with Elif("error"):
                    Muted(content="Apply failed — see error above.")
                with Elif("cancelled"):
                    Muted(content="Cancelled. No changes were made.")
                with Else():
                    Muted(content="This is a preview. No changes have been made.")
                _render_apply_button_row(
                    confirm_label="Confirm & Create",
                    apply_action=apply_action,
                    cancel_action=cancel_action,
                    direct_apply=True,
                )
            elif response.get("katana_url"):
                Button(
                    label="View in Katana",
                    variant="outline",
                    on_click=SendMessage(
                        f"Open {response['katana_url']} in the Katana web UI"
                    ),
                )
    return app


def build_stock_adjustment_update_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the update-stock-adjustment preview card with direct-apply rail.

    Renders the requested header field changes as a small DataTable so
    the user can sanity-check what's about to be patched.
    """
    is_preview = bool(response.get("is_preview"))
    diff_rows: list[dict[str, str]] = []
    for field, label in (
        ("stock_adjustment_number", "Number"),
        ("stock_adjustment_date", "Date"),
        ("location_id", "Location ID"),
        ("reason", "Reason"),
        ("additional_info", "Additional Info"),
    ):
        value = response.get(field)
        if value is not None:
            diff_rows.append({"field": label, "new_value": str(value)})

    state: dict[str, Any] = {"diff_rows": diff_rows}
    apply_action: list[Action] | None = None
    cancel_action: list[Action] | None = None
    if is_preview:
        state.update(_DIRECT_APPLY_STATE_INIT)
        apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
        cancel_action = _build_cancel_action("the stock-adjustment update")

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content="Update Stock Adjustment")
            if response.get("id") is not None:
                Badge(label=f"#{response['id']}", variant="outline")
            Badge(
                label="PREVIEW" if is_preview else "UPDATED",
                variant="secondary" if is_preview else "default",
            )

        with CardContent(), Column(gap=3):
            if response.get("message"):
                Text(content=response["message"])
            if diff_rows:
                DataTable(
                    columns=_STOCK_ADJUSTMENT_FIELD_DIFF_COLUMNS,
                    rows="{{ diff_rows }}",
                )
            else:
                Muted(content="No field changes supplied.")

            if is_preview:
                with If("error"):
                    Separator()
                    with Alert(variant="destructive", icon="circle-alert"):
                        AlertTitle(content="Apply failed")
                        AlertDescription(content="{{ error }}")

        with CardFooter(), Row(gap=2):
            if apply_action is not None and cancel_action is not None:
                with If("applied"):
                    Muted(content="Stock adjustment updated.")
                with Elif("error"):
                    Muted(content="Apply failed — see error above.")
                with Elif("cancelled"):
                    Muted(content="Cancelled. No changes were made.")
                with Else():
                    Muted(content="This is a preview. No changes have been made.")
                _render_apply_button_row(
                    confirm_label="Confirm & Update",
                    apply_action=apply_action,
                    cancel_action=cancel_action,
                    direct_apply=True,
                )
            elif response.get("katana_url"):
                Button(
                    label="View in Katana",
                    variant="outline",
                    on_click=SendMessage(
                        f"Open {response['katana_url']} in the Katana web UI"
                    ),
                )
    return app


def build_stock_adjustment_delete_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the delete-stock-adjustment preview card with direct-apply rail.

    Surfaces the identifying details (number, location, row count) so the
    user can sanity-check before confirming. Apply path reverses the
    associated inventory movements server-side — that consequence is
    called out in the footer copy.
    """
    is_preview = bool(response.get("is_preview"))
    state: dict[str, Any] = {}
    apply_action: list[Action] | None = None
    cancel_action: list[Action] | None = None
    if is_preview:
        state = dict(_DIRECT_APPLY_STATE_INIT)
        apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
        cancel_action = _build_cancel_action("the stock-adjustment deletion")

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content="Delete Stock Adjustment")
            if response.get("id") is not None:
                Badge(label=f"#{response['id']}", variant="outline")
            Badge(
                label="PREVIEW" if is_preview else "DELETED",
                variant="secondary" if is_preview else "destructive",
            )

        with CardContent(), Column(gap=3):
            if response.get("message"):
                Text(content=response["message"])

            with Row(gap=4):
                Metric(
                    label="Number",
                    value=str(response.get("stock_adjustment_number") or "—"),
                )
                Metric(
                    label="Location",
                    value=str(response.get("location_id") or "—"),
                )
                Metric(
                    label="Rows",
                    value=str(response.get("row_count", 0)),
                )

            if is_preview:
                Muted(
                    content=(
                        "Deleting reverses the associated inventory "
                        "movements server-side. This cannot be undone."
                    )
                )
                with If("error"):
                    Separator()
                    with Alert(variant="destructive", icon="circle-alert"):
                        AlertTitle(content="Apply failed")
                        AlertDescription(content="{{ error }}")

        with CardFooter(), Row(gap=2):
            if apply_action is not None and cancel_action is not None:
                with If("applied"):
                    Muted(content="Stock adjustment deleted.")
                with Elif("error"):
                    Muted(content="Apply failed — see error above.")
                with Elif("cancelled"):
                    Muted(content="Cancelled. No changes were made.")
                with Else():
                    Muted(content="This is a preview. No changes have been made.")
                _render_apply_button_row(
                    confirm_label="Confirm & Delete",
                    apply_action=apply_action,
                    cancel_action=cancel_action,
                    direct_apply=True,
                )
    return app


# ============================================================================
# Order UIs (Preview + Created)
# ============================================================================

OrderType = Literal["Purchase Order", "Sales Order", "Manufacturing Order"]
ItemAction = Literal["Created", "Updated", "Deleted"]


def _extract_order_fields(order: dict[str, Any]) -> dict[str, Any]:
    """Extract common display fields from an order dict."""
    total_cost = order.get("total_cost")
    return {
        "order_number": order.get("order_number") or order.get("order_no", "N/A"),
        "order_id": order.get("id", "N/A"),
        "total": total_cost if total_cost is not None else order.get("total"),
        "currency": order.get("currency", "USD"),
        "status": order.get("status", "CREATED"),
    }


def _render_order_fields(order: dict[str, Any], *, total: Any, currency: str) -> None:
    """Render shared order content fields (supplier/customer/location + total).

    Prefers human-readable names when present (``customer_name``,
    ``supplier_name``, ``location_name``) and falls back to bare IDs. If the
    order dict carries a non-empty ``notes`` key, it renders below the entity
    lines so the user can visually verify the value persisted on the apply
    card — matching the preview's information density (#618). Today only
    ``create_purchase_order``'s response model surfaces ``notes``; the other
    order responses expose the field as ``additional_info`` and don't feed it
    here, so the line is silently skipped for those tools.
    """
    if total is not None:
        Metric(label="Total", value=f"${total:,.2f} {currency}")

    if order.get("supplier_id"):
        name = order.get("supplier_name")
        Text(
            content=f"Supplier: {name} (ID: {order['supplier_id']})"
            if name
            else f"Supplier ID: {order['supplier_id']}"
        )
    if order.get("customer_id"):
        name = order.get("customer_name")
        Text(
            content=f"Customer: {name} (ID: {order['customer_id']})"
            if name
            else f"Customer ID: {order['customer_id']}"
        )
    if order.get("location_id"):
        name = order.get("location_name")
        Text(
            content=f"Location: {name} (ID: {order['location_id']})"
            if name
            else f"Location ID: {order['location_id']}"
        )
    if order.get("item_count") is not None:
        Text(content=f"Items: {order['item_count']}")
    notes = order.get("notes")
    if notes:
        Text(content=f"Notes: {notes}")


def build_order_preview_ui(
    order: dict[str, Any],
    order_type: OrderType,
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
    direct_apply: bool = False,
) -> PrefabApp:
    """Build an order preview card with confirm/cancel buttons.

    Pass the original Pydantic ``confirm_request`` and matching
    ``confirm_tool`` name. Two apply rails:

    - ``direct_apply=False`` (default) — Confirm fires a SendMessage chat
      hint and the agent re-issues the call. See ADR-0015.
    - ``direct_apply=True`` — Confirm fires ``tools/call`` directly, the
      iframe morphs in place to a result view, and the structured response
      is pushed to the agent via ``ui/update-model-context``. See ADR-0016
      (forthcoming). Currently opted into by ``create_purchase_order``;
      rolling out across the rest of the write tools after Cowork
      verification.
    """
    fields = _extract_order_fields(order)
    apply_action: list[Action] | CallTool | None
    if direct_apply:
        apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
    else:
        apply_action = _build_apply_action(confirm_tool, confirm_request)
    cancel_action = _build_cancel_action(f"that {order_type.lower()}")
    state: dict[str, Any] = {"order": order, "pending": False, "cancelled": False}
    if direct_apply:
        # Initial state for the morph; on apply success the iframe sets
        # `applied=True` and stashes the structured response in `result`.
        state["applied"] = False
        state["error"] = None
        state["result"] = None

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"{order_type} Preview")
            Badge(label=fields["order_number"], variant="outline")
            Badge(label="PREVIEW", variant="secondary")

        with CardContent(), Column(gap=3):
            _render_order_fields(
                order, total=fields["total"], currency=fields["currency"]
            )
            if order.get("variant_id"):
                Text(content=f"Variant ID: {order['variant_id']}")
            if order.get("planned_quantity"):
                Text(content=f"Planned Quantity: {order['planned_quantity']}")

            block_warnings, regular_warnings = _split_warnings(order.get("warnings"))
            if block_warnings or regular_warnings:
                Separator()
                for warning in block_warnings:
                    Badge(label=warning, variant="destructive")
                for warning in regular_warnings:
                    Badge(label=warning, variant="secondary")

            if direct_apply:
                # Direct-apply morph: success/error blocks render in place
                # of the preview footer messaging when the iframe state
                # flips. The agent has already received the structured
                # result via ui/update-model-context — these blocks are
                # for the user, not the agent.
                with If("applied"):
                    Separator()
                    Text(content=f"{order_type} created.")
                    Muted(
                        content=(
                            "The structured result has been pushed to the "
                            "assistant's context."
                        )
                    )
                with Elif("error"):
                    Separator()
                    with Alert(variant="destructive", icon="circle-alert"):
                        AlertTitle(content="Apply failed")
                        AlertDescription(content="{{ error }}")

        with CardFooter():
            if block_warnings:
                Muted(
                    content="Cannot proceed — see warnings above. No changes have been made."
                )
            elif direct_apply:
                # Footer message tracks the iframe state — once applied or
                # errored, "This is a preview" is no longer true and would
                # confuse the user.
                with If("applied"):
                    Muted(content=f"{order_type} created.")
                with Elif("error"):
                    Muted(content="Apply failed — see error above.")
                with Elif("cancelled"):
                    Muted(content="Cancelled. No changes were made.")
                with Else():
                    Muted(content="This is a preview. No changes have been made.")
            else:
                Muted(content="This is a preview. No changes have been made.")

            _render_apply_button_row(
                confirm_label=f"Confirm & Create {order_type}",
                apply_action=apply_action,
                cancel_action=cancel_action,
                disabled=bool(block_warnings),
                direct_apply=direct_apply,
            )
    return app


def build_order_created_ui(
    order: dict[str, Any],
    order_type: OrderType,
) -> PrefabApp:
    """Build a success card for a created order."""
    fields = _extract_order_fields(order)
    order_id = fields["order_id"]

    with PrefabApp(state={"order": order}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"{order_type} Created")
            Badge(label=fields["order_number"], variant="outline")
            Badge(label=fields["status"], variant="default")

        with CardContent(), Column(gap=2):
            Text(content=f"Order ID: {order_id}")
            _render_order_fields(
                order, total=fields["total"], currency=fields["currency"]
            )

        with CardFooter(), Row(gap=2):
            if order_type == "Purchase Order":
                Button(
                    label="Receive Items",
                    variant="outline",
                    on_click=SendMessage(
                        f"Receive items for purchase order {order_id}"
                    ),
                )
                Button(
                    label="Verify Document",
                    variant="outline",
                    on_click=SendMessage(
                        f"Verify a supplier document against PO {order_id}"
                    ),
                )
            elif order_type == "Sales Order":
                Button(
                    label="Fulfill Order",
                    variant="outline",
                    on_click=SendMessage(f"Fulfill sales order {order_id}"),
                )
            elif order_type == "Manufacturing Order":
                Button(
                    label="Complete Order",
                    variant="outline",
                    on_click=SendMessage(f"Complete manufacturing order {order_id}"),
                )
    return app


# ============================================================================
# Fulfillment & Receipt UIs
# ============================================================================


def _extract_fulfill_fields(
    response: dict[str, Any],
) -> tuple[str, str, str]:
    """Extract common fulfillment display fields."""
    return (
        response.get("order_type", "order").title(),
        response.get("order_number", "N/A"),
        response.get("status", "N/A"),
    )


def _render_inventory_updates(
    response: dict[str, Any], *, label: str = "Inventory Changes:"
) -> None:
    """Render inventory update list if present."""
    if response.get("inventory_updates"):
        Muted(content=label)
        for update in response["inventory_updates"]:
            Text(content=f"  {update}")


def build_fulfill_preview_ui(
    response: dict[str, Any],
) -> PrefabApp:
    """Build a fulfillment preview card.

    The "Confirm Fulfillment" button re-invokes ``fulfill_order`` with
    ``preview=False`` and the original ``order_id`` / ``order_type``
    inlined from the response. No LLM round-trip.
    """
    from katana_mcp.tools.foundation.orders import FulfillOrderRequest

    # `order_type_display` is .title()-cased ("Sales" / "Manufacturing") for
    # use in user-facing strings; `raw_order_type` is the lowercase enum
    # value ("sales" / "manufacturing") that FulfillOrderRequest expects.
    # Keep them named distinctly so a future edit can't quietly substitute
    # the display value into the request constructor.
    order_type_display, order_number, status = _extract_fulfill_fields(response)
    raw_order_type = response["order_type"]
    # Direct lookup, not .get() — FulfillOrderResponse declares both fields
    # required; a missing key signals a malformed response dict and we
    # want to fail at preview-build time, not at click time.
    confirm_request = FulfillOrderRequest(
        order_id=response["order_id"],
        order_type=raw_order_type,
        preview=True,
    )
    block_warnings, regular_warnings = _split_warnings(response.get("warnings"))
    apply_action = _build_apply_action("fulfill_order", confirm_request)
    cancel_action = _build_cancel_action(
        f"the {raw_order_type} order {order_number} fulfillment"
    )
    state = {"response": response, "pending": False, "cancelled": False}

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Fulfill {order_type_display} Order")
            Badge(label=order_number, variant="outline")
            Badge(label=status, variant="secondary")

        with CardContent(), Column(gap=2):
            _render_inventory_updates(response)

            if block_warnings or regular_warnings:
                Separator()
                for warning in block_warnings:
                    Badge(label=warning, variant="destructive")
                for warning in regular_warnings:
                    Badge(label=warning, variant="secondary")

        with CardFooter():
            _render_apply_button_row(
                confirm_label="Confirm Fulfillment",
                apply_action=apply_action,
                cancel_action=cancel_action,
                disabled=bool(block_warnings),
            )
    return app


def build_fulfill_success_ui(
    response: dict[str, Any],
) -> PrefabApp:
    """Build a fulfillment success card."""
    order_type, order_number, status = _extract_fulfill_fields(response)

    with PrefabApp(state={"response": response}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"{order_type} Order Fulfilled")
            Badge(label=order_number, variant="outline")
            Badge(label=status, variant="default")

        with CardContent(), Column(gap=2):
            if response.get("message"):
                Text(content=response["message"])
            if response.get("inventory_updates"):
                Separator()
            _render_inventory_updates(response, label="Inventory Updates:")

        with CardFooter():
            Button(
                label="Check Inventory",
                variant="outline",
                on_click=SendMessage("Check current inventory levels"),
            )
    return app


# ============================================================================
# Verification UI
# ============================================================================


def build_verification_ui(
    response: dict[str, Any],
) -> PrefabApp:
    """Build a verification results card with matches and discrepancies."""
    overall_status = response.get("overall_status", "unknown")

    status_variant = {
        "match": "default",
        "partial_match": "secondary",
        "no_match": "destructive",
    }.get(overall_status, "secondary")

    matches = response.get("matches", [])
    discrepancies = response.get("discrepancies", [])

    with (
        PrefabApp(
            state={"matches": matches, "discrepancies": discrepancies},
            css_class="p-4",
        ) as app,
        Column(gap=4),
    ):
        with Row(gap=2):
            H3(content="Document Verification")
            Badge(label=f"PO {response.get('order_id', 'N/A')}", variant="outline")
            Badge(
                label=overall_status.replace("_", " ").title(), variant=status_variant
            )

        # Matches table
        if matches:
            Muted(content="Matched Items:")
            DataTable(
                columns=[
                    DataTableColumn(key="sku", header="SKU", sortable=True),
                    DataTableColumn(key="quantity", header="Quantity", align="right"),
                    DataTableColumn(key="unit_price", header="Price", align="right"),
                    DataTableColumn(key="status", header="Status"),
                ],
                rows="{{ matches }}",
            )

        # Discrepancies table
        if discrepancies:
            Muted(content="Discrepancies:")
            DataTable(
                columns=[
                    DataTableColumn(key="sku", header="SKU"),
                    DataTableColumn(key="type", header="Type"),
                    DataTableColumn(key="message", header="Details"),
                ],
                rows="{{ discrepancies }}",
            )

        # Action buttons
        with Row(gap=2):
            if overall_status == "match":
                Button(
                    label="Proceed to Receive",
                    variant="default",
                    on_click=SendMessage(
                        f"Receive items for purchase order {response.get('order_id', '')}"
                    ),
                )
            else:
                Button(
                    label="Receive Anyway",
                    variant="outline",
                    on_click=SendMessage(
                        f"Receive items for purchase order {response.get('order_id', '')} "
                        "despite discrepancies"
                    ),
                )
    return app


# ============================================================================
# Generic Modification Preview/Result UIs (modify_*/delete_*/correct_*)
# ============================================================================


# Display labels for the verb in modification card titles. The verb is
# derived from the registered tool name (its first underscore-delimited
# token), so ``modify_item`` → "Modify", ``delete_item`` → "Delete", etc.
# Fallback for unrecognized verbs is "Modify" so the title still reads
# sensibly even if a new tool prefix is introduced before this map is
# updated.
_VERB_DISPLAY: dict[str, str] = {
    "modify": "Modify",
    "delete": "Delete",
    "correct": "Correct",
    "update": "Update",
}


def _humanize_snake_case(raw: str) -> str:
    """Convert a snake_case identifier to a Title Case display label."""
    return raw.replace("_", " ").title()


def _verb_label(tool_name: str | None) -> str:
    """Pick the human-readable verb for the modification card title.

    Used to render ``"Modify Product"`` / ``"Delete Product"`` /
    ``"Correct Purchase Order"`` titles correctly across the modification
    rail. ``None`` (or any unrecognized prefix) falls back to "Modify".
    """
    if not tool_name:
        return "Modify"
    return _VERB_DISPLAY.get(tool_name.split("_", 1)[0], "Modify")


# Single column set used by both preview and result modification cards.
# One row per planned action — server-derived ``status_label`` and
# ``summary`` fields land directly here so the apply path's
# ``SetState("plan_actions", RESULT.actions)`` swap preserves shape.
_ACTION_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="index", header="#", width="3rem"),
    DataTableColumn(key="operation_label", header="Operation"),
    DataTableColumn(key="target_label", header="Target"),
    DataTableColumn(key="summary", header="Changes"),
    DataTableColumn(key="status_label", header="Status"),
]

_PLAN_ACTIONS_KEY = "plan_actions"
# DataTable.rows requires the mustache template form (``{{ key }}``) for
# state-bound rows — the JS renderer interprets bare strings as the rows
# array itself and crashes with ``t.some is not a function``. Discovered
# via headless apps_dev render tests after #634; the Python pydantic
# field type accepts bare strings, but the wire format only resolves
# mustache references.
_PLAN_ACTIONS_REF = f"{{{{ {_PLAN_ACTIONS_KEY} }}}}"


def _derive_status_label(action: dict[str, Any]) -> str:
    """Compute a status label from raw ``succeeded`` / ``verified`` fields.

    Used as a fallback for action dicts that don't already carry the
    server-derived ``status_label`` (legacy responses, older clients,
    test fixtures). Mirrors
    :func:`katana_mcp.tools._modification._derive_status_label`.
    """
    succeeded = action.get("succeeded")
    if succeeded is None:
        return "PLANNED"
    if succeeded is True:
        verified = action.get("verified")
        if verified is False:
            return "APPLIED (verification mismatch)"
        if verified is True:
            return "APPLIED (verified)"
        return "APPLIED"
    return "FAILED"


def _derive_summary(action: dict[str, Any]) -> str:
    """Fallback summary derivation when the action lacks a server-supplied one."""
    op = str(action.get("operation") or "").lower()
    changes = action.get("changes") or []
    if op.startswith("delete"):
        return "deleted"
    if op.startswith("add") or op.startswith("create"):
        return f"{len(changes)} field(s) set"
    n_changed = sum(
        1 for c in changes if isinstance(c, dict) and not c.get("is_unchanged")
    )
    if n_changed == 0 and changes:
        return f"{len(changes)} field(s) — no change"
    return f"{n_changed} field(s) changed"


def _action_to_row(idx: int, action: dict[str, Any]) -> dict[str, Any]:
    """Project one ActionResult dict into a DataTable row.

    Returns a dict that carries display-only derived fields (``index``,
    ``operation_label``, ``target_label``) on top of the underlying
    ActionResult fields. Pre-populating the same shape both at preview-
    build time and on the apply RESULT means the on_success
    ``SetState("plan_actions", RESULT.actions)`` swap doesn't need any
    transformation — the server's ``status_label``/``summary`` already
    travel on every ActionResult.

    Falls back to local derivation when ``status_label``/``summary`` are
    absent (legacy single-action shape, older response generators, tests).
    """
    target = action.get("target_id")
    return {
        "index": action.get("index") or idx,
        "operation_label": action.get("operation_label")
        or (_humanize_snake_case(str(action.get("operation") or "")) or "Action"),
        "target_label": action.get("target_label")
        or (f"#{target}" if target is not None else "—"),
        "summary": action.get("summary") or _derive_summary(action),
        "status_label": action.get("status_label") or _derive_status_label(action),
        # Pass through the underlying fields so RESULT.actions replacement
        # preserves shape (the server's ActionResults carry these too).
        "operation": action.get("operation"),
        "target_id": target,
        "succeeded": action.get("succeeded"),
        "verified": action.get("verified"),
        "error": action.get("error"),
    }


def _legacy_action(response: dict[str, Any]) -> dict[str, Any] | None:
    """Synthesize a single ActionResult-shaped dict from the legacy shape.

    The legacy single-action response carries top-level ``operation`` +
    ``changes`` (instead of an ``actions`` list). Wrap it as one synthetic
    action so both card builders flow through the same row builder.
    """
    legacy_changes = response.get("changes") or []
    legacy_op = response.get("operation") or ""
    if not legacy_op and not legacy_changes:
        return None
    is_preview = bool(response.get("is_preview"))
    n = len(legacy_changes)
    return {
        "operation": legacy_op,
        "target_id": response.get("entity_id"),
        "changes": legacy_changes,
        "succeeded": None if is_preview else True,
        "verified": None,
        "error": None,
        "status_label": "PLANNED" if is_preview else "APPLIED",
        "summary": f"{n} field(s) changed" if n else "—",
    }


def _actions_to_rows(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map ActionResult dicts to DataTable rows for ``state.plan_actions``."""
    return [_action_to_row(idx, action) for idx, action in enumerate(actions, start=1)]


def _count_outcomes(actions: list[dict[str, Any]]) -> tuple[int, int]:
    """Tally ``(succeeded, failed)`` across an action list."""
    s = sum(1 for a in actions if a.get("succeeded") is True)
    f = sum(1 for a in actions if a.get("succeeded") is False)
    return s, f


def build_modification_preview_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Preview card for a :class:`ModificationResponse` with the direct-apply rail.

    Used by every tool that returns a ``ModificationResponse`` from
    ``_modification.py`` — ``modify_*``, ``delete_*``, ``correct_*``.

    The card renders **one DataTable** bound to ``state.plan_actions``
    (one row per planned action: # / Operation / Target / Changes / Status).
    Confirm fires ``tools/call`` directly; the on_success chain pushes
    ``RESULT.actions`` into ``state.plan_actions`` so each row's status
    cell ticks PLANNED → APPLIED/FAILED in place without re-rendering
    the iframe (ADR-0016 direct-apply rail). The iframe also pushes the
    structured result to the agent via ``ui/update-model-context``.
    """
    actions = response.get("actions") or []
    if not actions:
        legacy = _legacy_action(response)
        if legacy is not None:
            actions = [legacy]

    apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
    # NOTE: A live-tick design (rows ticking PLANNED -> APPLIED in place via
    # ``SetState("plan_actions", RESULT.actions)``) was attempted in #634 but
    # turned out to be broken: ``$result`` in the on_success Rx context
    # resolves to the apply tool's ``structured_content`` (a PrefabApp wire
    # envelope from ``make_tool_result``), not to the raw
    # ``ModificationResponse``. ``$result.actions`` therefore doesn't
    # resolve and the SetState was a no-op in production. Caught by Copilot
    # review; verified by the browser harness when its stub was switched to
    # match production shape. Tracked as a follow-up — until then the
    # apply path morphs the card via the existing ``applied=True`` flag.
    entity_type_raw = str(response.get("entity_type") or "entity")
    entity_type_label = _humanize_snake_case(entity_type_raw)
    verb_label = _verb_label(confirm_tool)
    cancel_action = _build_cancel_action(
        f"the {entity_type_raw.replace('_', ' ')} {verb_label.lower()}"
    )

    block_warnings, regular_warnings = _split_warnings(response.get("warnings"))
    n_actions = len(actions)

    state: dict[str, Any] = {
        "pending": False,
        "cancelled": False,
        "applied": False,
        "error": None,
        _PLAN_ACTIONS_KEY: _actions_to_rows(actions),
    }

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            title_suffix = f" — {n_actions} action(s)" if n_actions > 0 else ""
            CardTitle(content=f"{verb_label} {entity_type_label}{title_suffix}")
            entity_id = response.get("entity_id")
            if entity_id is not None:
                Badge(label=f"#{entity_id}", variant="outline")
            Badge(label="PREVIEW", variant="secondary")

        with CardContent(), Column(gap=3):
            if response.get("message"):
                Text(content=response["message"])

            if n_actions > 0:
                DataTable(columns=_ACTION_COLUMNS, rows=_PLAN_ACTIONS_REF)

            if block_warnings or regular_warnings:
                Separator()
                for warning in block_warnings:
                    Badge(label=warning, variant="destructive")
                for warning in regular_warnings:
                    Badge(label=warning, variant="secondary")

            with If("error"):
                Separator()
                with Alert(variant="destructive", icon="circle-alert"):
                    AlertTitle(content="Apply failed")
                    AlertDescription(content="{{ error }}")

        with CardFooter():
            if block_warnings:
                Muted(
                    content="Cannot proceed — see warnings above. No changes have been made."
                )
            else:
                with If("applied"):
                    Muted(
                        content="Changes applied — see status column for per-action outcome."
                    )
                with Elif("error"):
                    Muted(content="Apply failed — see error above.")
                with Elif("cancelled"):
                    Muted(content="Cancelled. No changes were made.")
                with Else():
                    Muted(content="This is a preview. No changes have been made.")

            confirm_label = (
                f"Confirm {n_actions} action(s)" if n_actions > 1 else "Confirm Changes"
            )
            _render_apply_button_row(
                confirm_label=confirm_label,
                apply_action=apply_action,
                cancel_action=cancel_action,
                disabled=bool(block_warnings),
                direct_apply=True,
            )
    return app


def build_modification_result_ui(
    response: dict[str, Any], *, tool_name: str | None = None
) -> PrefabApp:
    """Result card for an *applied* :class:`ModificationResponse`.

    Mirrors :func:`build_modification_preview_ui` but without Confirm/Cancel
    — every action carries its terminal status (APPLIED / APPLIED (verified) /
    APPLIED (verification mismatch) / FAILED) and the card surfaces the
    aggregate outcome plus a "View in Katana" button when a ``katana_url``
    is present (deletes successfully applied null out the URL upstream).

    ``tool_name`` is the registered MCP tool name (e.g. ``"delete_item"``) —
    used to derive the title's verb so a successful delete reads "Product
    Delete" rather than the misleading "Product Modification". Optional
    for backwards compatibility with the legacy single-action shape, which
    falls back to the response's top-level ``operation`` field.
    """
    entity_type_label = _humanize_snake_case(
        str(response.get("entity_type") or "entity")
    )
    actions = response.get("actions") or []
    legacy_op = _humanize_snake_case(str(response.get("operation") or ""))
    if not actions:
        legacy = _legacy_action(response)
        if legacy is not None:
            actions = [legacy]

    success_count, failed_count = _count_outcomes(actions)

    overall_status: str
    overall_variant: Literal["default", "secondary", "outline", "destructive"]
    if failed_count > 0 and success_count > 0:
        overall_status, overall_variant = "PARTIAL FAILURE", "destructive"
    elif failed_count > 0:
        overall_status, overall_variant = "FAILED", "destructive"
    else:
        overall_status, overall_variant = "APPLIED", "default"

    state: dict[str, Any] = {_PLAN_ACTIONS_KEY: _actions_to_rows(actions)}

    # Title verb: prefer the tool-derived verb (works for delete/correct
    # tools); fall back to the legacy single-action ``operation`` field;
    # finally to a neutral "Modification".
    if tool_name:
        title_op = _verb_label(tool_name)
    else:
        title_op = legacy_op or "Modification"

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"{entity_type_label} {title_op}")
            entity_id = response.get("entity_id")
            if entity_id is not None:
                Badge(label=f"#{entity_id}", variant="outline")
            Badge(label=overall_status, variant=overall_variant)

        with CardContent(), Column(gap=3):
            if response.get("message"):
                Text(content=response["message"])

            if actions:
                Muted(
                    content=(
                        f"{success_count} succeeded, {failed_count} failed "
                        f"of {len(actions)}"
                    )
                )
                DataTable(columns=_ACTION_COLUMNS, rows=_PLAN_ACTIONS_REF)

        if response.get("katana_url"):
            with CardFooter(), Row(gap=2):
                Button(
                    label="View in Katana",
                    variant="outline",
                    on_click=SendMessage(
                        f"Open {response['katana_url']} in the Katana web UI"
                    ),
                )
    return app


# ============================================================================
# Item Created/Updated/Deleted UIs
# ============================================================================


def build_item_mutation_ui(
    item: dict[str, Any],
    action: ItemAction,
) -> PrefabApp:
    """Build a card for item created/updated/deleted responses."""
    with PrefabApp(state={"item": item}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Item {action}")
            if item.get("type"):
                Badge(label=str(item["type"]), variant="secondary")

        with CardContent(), Column(gap=2):
            Text(content=f"ID: {item.get('id', 'N/A')}")
            Text(content=f"Name: {item.get('name', 'N/A')}")
            if item.get("sku"):
                Text(content=f"SKU: {item['sku']}")
            if item.get("message"):
                Text(content=item["message"])

        with CardFooter(), Row(gap=2):
            if item.get("sku"):
                Button(
                    label="View Details",
                    variant="outline",
                    on_click=SendMessage(f"Get variant details for SKU {item['sku']}"),
                )
            if item.get("sku"):
                Button(
                    label="Check Inventory",
                    variant="outline",
                    on_click=SendMessage(f"Check inventory for SKU {item['sku']}"),
                )
    return app


# ============================================================================
# Receipt UI
# ============================================================================


def build_receipt_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel | None = None,
    confirm_tool: str | None = None,
) -> PrefabApp:
    """Build a receipt card for received purchase order items.

    On the preview branch, pass ``confirm_request`` (the original Pydantic
    input) and ``confirm_tool`` (the matching tool name) to wire the
    "Confirm Receipt" button. Both kwargs are optional because the same
    builder is reused for the non-preview render where no confirm button
    is shown — must be set together (enforced by ``_build_apply_action``).
    """
    order_number = response.get("order_number", "N/A")
    is_preview = response.get("is_preview", True)
    apply_action = _build_apply_action(confirm_tool, confirm_request)
    cancel_action = _build_cancel_action(f"the receipt for {order_number}")
    state: dict[str, Any] = {
        "response": response,
        "pending": False,
        "cancelled": False,
    }

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content="Purchase Order Receipt")
            Badge(label=order_number, variant="outline")
            Badge(
                label="PREVIEW" if is_preview else "RECEIVED",
                variant="secondary" if is_preview else "default",
            )

        with CardContent(), Column(gap=2):
            if response.get("message"):
                Text(content=response["message"])
            Metric(
                label="Items Received",
                value=str(response.get("items_received", 0)),
            )
            if response.get("status"):
                Text(content=f"PO Status: {response['status']}")
            if response.get("supplier_id"):
                name = response.get("supplier_name")
                Text(
                    content=f"Supplier: {name} (ID: {response['supplier_id']})"
                    if name
                    else f"Supplier ID: {response['supplier_id']}"
                )
            if response.get("total_cost") is not None:
                Metric(
                    label="PO Total",
                    value=f"${response['total_cost']:,.2f} {response.get('currency') or 'USD'}",
                )

            block_warnings, regular_warnings = _split_warnings(response.get("warnings"))
            if block_warnings or regular_warnings:
                Separator()
                for warning in block_warnings:
                    Badge(label=warning, variant="destructive")
                for warning in regular_warnings:
                    Badge(label=warning, variant="secondary")

        with CardFooter():
            if is_preview and apply_action is not None:
                _render_apply_button_row(
                    confirm_label="Confirm Receipt",
                    apply_action=apply_action,
                    cancel_action=cancel_action,
                    disabled=bool(block_warnings),
                )
            else:
                Button(
                    label="Check Inventory",
                    variant="outline",
                    on_click=SendMessage(
                        "Check current inventory levels after receipt"
                    ),
                )
    return app


# ============================================================================
# Batch Recipe Update UI
# ============================================================================


def build_batch_recipe_update_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel | None = None,
    confirm_tool: str | None = None,
) -> PrefabApp:
    """Build a batch recipe update card with per-group tables and summary metrics.

    Shows one row per planned sub-op grouped by replacement group_label.
    Preview mode shows all ops as PENDING; executed mode shows SUCCESS/FAILED/SKIPPED.

    On the preview branch, pass ``confirm_request`` (the original Pydantic
    input) and ``confirm_tool`` (the matching tool name) to wire the
    "Execute batch" button. Both kwargs are optional because the same
    builder is reused for the non-preview render — must be set together
    (enforced by ``_build_apply_action``).
    """
    is_preview = response.get("is_preview", True)
    results = response.get("results", [])
    warnings = response.get("warnings", [])
    message = response.get("message", "")

    # Group sub-ops by group_label for display
    groups: dict[str, list[dict[str, Any]]] = {}
    for op in results:
        label = op.get("group_label") or "Other"
        groups.setdefault(label, []).append(op)

    # Augment each row with display-friendly fields (flatten nested structure)
    flat_rows: list[dict[str, Any]] = []
    for label, ops in groups.items():
        for op in ops:
            sku_or_variant = op.get("sku") or (
                f"variant {op['variant_id']}" if op.get("variant_id") else ""
            )
            flat_rows.append(
                {
                    "group": label,
                    "mo_id": op.get("manufacturing_order_id"),
                    "action": (op.get("op_type") or "").upper(),
                    "row_id": op.get("recipe_row_id") or "(new)",
                    "sku": sku_or_variant,
                    "qty": op.get("planned_quantity_per_unit") or "",
                    "status": (op.get("status") or "pending").upper(),
                    "error": op.get("error") or "",
                }
            )

    total = response.get("total_ops", 0)
    success = response.get("success_count", 0)
    failed = response.get("failed_count", 0)
    skipped = response.get("skipped_count", 0)

    mode_label = "PREVIEW" if is_preview else "RESULTS"
    mode_variant = (
        "secondary" if is_preview else ("destructive" if failed > 0 else "default")
    )

    state: dict[str, Any] = {
        "rows": flat_rows,
        "summary": {
            "total": total,
            "success": success,
            "failed": failed,
            "skipped": skipped,
        },
        "is_preview": is_preview,
        "warnings": warnings,
        "groups": list(groups.keys()),
        "pending": False,
        "cancelled": False,
    }
    apply_action = _build_apply_action(confirm_tool, confirm_request)
    cancel_action = _build_cancel_action(
        f"the batch recipe update ({total} planned operation(s))"
    )

    with (
        PrefabApp(
            state=state,
            css_class="p-4",
        ) as app,
        Column(gap=4),
    ):
        with Row(gap=2):
            H3(content="Batch Recipe Edits")
            Badge(label=mode_label, variant=mode_variant)
            Badge(label=f"{total} ops", variant="outline")

        with Row(gap=4):
            Metric(label="Total", value=str(total))
            if not is_preview:
                Metric(label="Success", value=str(success))
                Metric(label="Failed", value=str(failed))
                Metric(label="Skipped", value=str(skipped))

        # One big table with all ops, grouped visually by the group column
        DataTable(
            columns=[
                DataTableColumn(key="group", header="Group", sortable=True),
                DataTableColumn(key="mo_id", header="MO", sortable=True),
                DataTableColumn(key="action", header="Action"),
                DataTableColumn(key="row_id", header="Row ID"),
                DataTableColumn(key="sku", header="SKU"),
                DataTableColumn(key="qty", header="Qty", align="right"),
                DataTableColumn(key="status", header="Status", sortable=True),
                DataTableColumn(key="error", header="Error"),
            ],
            rows="{{ rows }}",
            search=True,
            paginated=True,
            pageSize=25,
        )

        if warnings:
            Muted(content=f"Warnings ({len(warnings)}):")
            for w in warnings:
                Text(content=f"- {w}")

        Text(content=message)

        # Action buttons
        if is_preview and apply_action is not None:
            _render_apply_button_row(
                confirm_label="Execute batch",
                apply_action=apply_action,
                cancel_action=cancel_action,
                disabled=False,
            )
        elif failed > 0:
            with Row(gap=2):
                Button(
                    label="Review failed ops",
                    variant="outline",
                    on_click=SendMessage(
                        "List the failed sub-operations from the last batch update "
                        "and suggest recovery steps"
                    ),
                )
        else:
            with Row(gap=2):
                Button(
                    label="Verify recipes",
                    variant="outline",
                    on_click=SendMessage(
                        "Verify the updated manufacturing order recipes"
                    ),
                )

    return app


# ============================================================================
# Generic Apply-Result UIs
# ============================================================================


def build_apply_success_ui(
    *,
    title: str,
    summary_lines: list[str],
    katana_url: str | None = None,
) -> PrefabApp:
    """Generic success card for an applied (non-preview) write operation.

    ``title`` is the card title (e.g. ``"Sales order #WEB20387 fulfilled"``).
    ``summary_lines`` are rendered verbatim as ``Text`` rows in the card
    body. ``katana_url``, when set, surfaces a "View in Katana" link button
    in the footer.
    """
    with PrefabApp(state={}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=title)
            Badge(label="APPLIED", variant="default")

        with CardContent(), Column(gap=2):
            for line in summary_lines:
                Text(content=line)

        if katana_url:
            with CardFooter(), Row(gap=2):
                Button(
                    label="View in Katana",
                    variant="outline",
                    on_click=SendMessage(f"Open {katana_url} in the Katana web UI"),
                )
    return app


def build_apply_error_ui(
    *,
    operation: str,
    error_message: str,
    hint: str | None = None,
) -> PrefabApp:
    """Generic error card for a failed (non-preview) write operation.

    Surfaces the actual error reason verbatim — closes #545 by ensuring
    the apply error is never swallowed by a static "failed" string.
    ``operation`` is a human-readable phrase like
    ``"Fulfilling sales order #WEB20387"``. ``hint``, when set, renders
    a remediation suggestion (e.g. ``"Check the supplier ID"``).
    """
    with PrefabApp(state={}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"{operation} failed")
            Badge(label="ERROR", variant="destructive")

        with CardContent(), Column(gap=2):
            with Alert(variant="destructive", icon="circle-alert"):
                AlertTitle(content="Error")
                AlertDescription(content=error_message)
            if hint:
                Muted(content=hint)
    return app
