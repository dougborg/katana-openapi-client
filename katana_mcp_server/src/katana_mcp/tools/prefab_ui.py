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
from prefab_ui.actions.mcp import CallTool, SendMessage
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    H3,
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
from prefab_ui.components.control_flow import ForEach
from prefab_ui.components.slot import Slot
from prefab_ui.rx import RESULT
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


def call_tool_from_request(
    tool_name: str,
    request: BaseModel,
    *,
    overrides: dict[str, Any] | None = None,
    on_success: Action | list[Action] | None = None,
    on_error: Action | list[Action] | None = None,
) -> CallTool:
    """Build a CallTool action that re-invokes ``tool_name`` with the
    request's fields **inlined as literal values** (not template strings).

    The action's ``arguments`` dict is built from ``request.model_dump(mode="json")``
    so the values are baked in at preview-render time. When the user clicks
    the rendered button, the host invokes the tool with the exact values
    the preview was based on — no host-side template substitution required.

    ``overrides`` (e.g. ``{"preview": False}``) take precedence over the
    inlined values — use them to flip a flag or substitute a literal at
    re-invocation time (typically to switch from preview to apply).

    ``on_success`` and ``on_error`` are passed through to the underlying
    ``CallTool`` so callers can chain feedback handlers (toast, state
    update, message) onto the apply call. Without these, the click fires
    invisibly — see #495 for why every Confirm button needs them.

    History: this helper used to emit Mustache-style ``{{ request.<field> }}``
    template strings and rely on the iframe host to substitute them from
    seeded state at click time. That host-side substitution silently failed
    in production (#491), arriving at the server with templated args
    dropped to null/empty — silent data corruption. Inlining values at
    build time bypasses the host-templating path entirely.
    """
    args: dict[str, Any] = request.model_dump(mode="json")
    if overrides:
        # Validate overrides against the keys actually being emitted, so a
        # caller can't silently smuggle an unknown field into the tool's
        # arguments. This stays in lockstep with model_dump's output even
        # if a future model adds computed fields or model_post_init magic.
        bad = sorted(set(overrides) - set(args))
        if bad:
            raise ValueError(
                f"Invalid override field(s) for {type(request).__name__}: "
                f"{', '.join(bad)}"
            )
        args.update(overrides)
    return CallTool(
        tool_name,
        arguments=args,
        on_success=on_success,
        on_error=on_error,
    )


def _build_confirm_action(
    confirm_tool: str,
    confirm_request: BaseModel,
    *,
    success_message: str,
    success_chat: str,
    error_message: str,
    error_chat: str,
) -> CallTool:
    """Construct the standard Confirm-button apply action with feedback
    handlers attached.

    Centralizes the visible-feedback contract for all preview UIs (#495):
    every Confirm button must surface a toast on success/error AND push a
    SendMessage so the apply call shows up in chat history. Without these
    handlers the click fires invisibly — the tool runs at the API but the
    user sees nothing. Result data is also captured into iframe state at
    ``state.result`` so a follow-up iteration can swap the preview content
    for a submitted/result card without another round-trip.

    All four message strings are baked in at preview-build time (no
    ``{{ ... }}`` template substitution required); this avoids the host
    substitution failure mode documented in #491.
    """
    return call_tool_from_request(
        confirm_tool,
        confirm_request,
        overrides={"preview": False},
        on_success=[
            SetState("result", RESULT),
            ShowToast(message=success_message, variant="success"),
            SendMessage(success_chat),
        ],
        on_error=[
            ShowToast(message=error_message, variant="error"),
            SendMessage(error_chat),
        ],
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

        DataTable(
            columns=[
                DataTableColumn(key="sku", header="SKU", sortable=True),
                DataTableColumn(key="name", header="Name", sortable=True),
                DataTableColumn(
                    key="is_sellable",
                    header="Sellable",
                    sortable=True,
                ),
            ],
            rows="items",
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


def build_variant_details_ui(
    variant: dict[str, Any],
) -> PrefabApp:
    """Build a detail card for a variant."""
    with PrefabApp(state={"variant": variant}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=variant.get("name", "Unknown"))
            Badge(label=variant.get("sku", ""), variant="outline")
            if variant.get("type"):
                Badge(
                    label=variant["type"],
                    variant="secondary",
                )

        with CardContent(), Column(gap=3):
            with Row(gap=4):
                Metric(
                    label="Sales Price",
                    value=f"${variant.get('sales_price', 0):,.2f}"
                    if variant.get("sales_price") is not None
                    else "N/A",
                )
                Metric(
                    label="Purchase Price",
                    value=f"${variant.get('purchase_price', 0):,.2f}"
                    if variant.get("purchase_price") is not None
                    else "N/A",
                )

            Separator()

            with Row(gap=4):
                Text(content=f"ID: {variant.get('id', 'N/A')}")
                if variant.get("product_id"):
                    Text(content=f"Product ID: {variant['product_id']}")
                if variant.get("material_id"):
                    Text(content=f"Material ID: {variant['material_id']}")
                if variant.get("lead_time") is not None:
                    Text(content=f"Lead Time: {variant['lead_time']} days")

            if variant.get("supplier_item_codes"):
                Muted(content="Supplier Codes:")
                with ForEach("variant.supplier_item_codes"):
                    Text(content="{{ $item }}")

        with CardFooter(), Row(gap=2):
            Button(
                label="Check Inventory",
                variant="outline",
                on_click=SendMessage(
                    f"Check inventory for SKU {variant.get('sku', '')}"
                ),
            )
            Button(
                label="Create Purchase Order",
                variant="outline",
                on_click=SendMessage(
                    f"Draft a purchase order for SKU {variant.get('sku', '')}"
                ),
            )
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
    with PrefabApp(state={"stock": stock}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=stock.get("product_name", "Unknown"))
            Badge(label=stock.get("sku", ""), variant="outline")

        with CardContent(), Row(gap=4):
            Metric(label="In Stock", value=str(stock.get("in_stock", 0)))
            Metric(label="Available", value=str(stock.get("available_stock", 0)))
            Metric(label="Committed", value=str(stock.get("committed", 0)))
            Metric(label="Expected", value=str(stock.get("expected", 0)))

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
    """Build a low stock report with table and reorder action."""
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
            rows="items",
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
    ``supplier_name``, ``location_name``) and falls back to bare IDs.
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


def build_order_preview_ui(
    order: dict[str, Any],
    order_type: OrderType,
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build an order preview card with confirm/cancel buttons.

    Pass ``confirm_request`` (the original Pydantic input) and
    ``confirm_tool`` (the matching tool name); the builder constructs the
    ``CallTool`` action with the request's fields inlined as literal
    values plus ``preview=False`` so the Confirm button re-invokes the
    tool directly without an LLM round-trip. See #491 for why values are
    inlined rather than templated from iframe state.
    """
    fields = _extract_order_fields(order)
    order_number = fields["order_number"]
    confirm_action = _build_confirm_action(
        confirm_tool,
        confirm_request,
        success_message=f"{order_type} {order_number} created",
        success_chat=f"{order_type} {order_number} was created successfully.",
        error_message=f"{order_type} creation failed",
        error_chat=(
            f"{order_type} {order_number} creation failed — please review "
            "the error and try again."
        ),
    )
    state: dict[str, Any] = {"order": order, "result": None}

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

        with CardFooter():
            if block_warnings:
                Muted(
                    content="Cannot proceed — see warnings above. No changes have been made."
                )
            else:
                Muted(content="This is a preview. No changes have been made.")

            with Row(gap=2):
                if not block_warnings:
                    Button(
                        label="Confirm & Create",
                        variant="default",
                        on_click=confirm_action,
                    )
                Button(
                    label="Cancel",
                    variant="outline",
                    on_click=ShowToast(
                        message=f"{order_type} creation cancelled",
                        variant="info",
                    ),
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

    The "Confirm Fulfillment" button invokes ``fulfill_order`` directly via
    ``CallTool`` with ``preview=False`` and the original order_id/order_type
    inlined as literal values from the response (see #491 — host-side
    template substitution silently drops args, so values are baked in at
    build time instead). No LLM round-trip.
    """
    order_type, order_number, status = _extract_fulfill_fields(response)
    # Use direct lookup, not .get() — FulfillOrderResponse declares both
    # fields required, so a missing key here means a malformed response
    # dict reached the builder. Fail at preview-build time rather than
    # generating a Confirm button that would invoke the tool with
    # ``order_id=None``.
    order_id = response["order_id"]
    raw_order_type = response["order_type"]

    with (
        PrefabApp(state={"response": response, "result": None}, css_class="p-4") as app,
        Card(),
    ):
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Fulfill {order_type} Order")
            Badge(label=order_number, variant="outline")
            Badge(label=status, variant="secondary")

        with CardContent(), Column(gap=2):
            _render_inventory_updates(response)

            block_warnings, regular_warnings = _split_warnings(response.get("warnings"))
            if block_warnings or regular_warnings:
                Separator()
                for warning in block_warnings:
                    Badge(label=warning, variant="destructive")
                for warning in regular_warnings:
                    Badge(label=warning, variant="secondary")

        with CardFooter(), Row(gap=2):
            if not block_warnings:
                # Same feedback contract as the helper-built confirm
                # actions (#495): toast + state capture + chat-side
                # SendMessage so the click produces visible signal
                # everywhere a user might be looking. Hand-built here
                # because the args aren't a Pydantic request — they're
                # echoed from the response dict.
                Button(
                    label="Confirm Fulfillment",
                    variant="default",
                    on_click=CallTool(
                        "fulfill_order",
                        arguments={
                            "order_id": order_id,
                            "order_type": raw_order_type,
                            "preview": False,
                        },
                        on_success=[
                            SetState("result", RESULT),
                            ShowToast(
                                message=f"{order_type} order {order_number} fulfilled",
                                variant="success",
                            ),
                            SendMessage(
                                f"{order_type} order {order_number} was fulfilled "
                                "successfully; inventory has been updated."
                            ),
                        ],
                        on_error=[
                            ShowToast(
                                message=f"Fulfillment for {order_number} failed",
                                variant="error",
                            ),
                            SendMessage(
                                f"Fulfilling {order_type.lower()} order {order_number} "
                                "failed — please review the error and try again."
                            ),
                        ],
                    ),
                )
            Button(
                label="Cancel",
                variant="outline",
                on_click=ShowToast(message="Fulfillment cancelled", variant="info"),
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
                rows="matches",
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
                rows="discrepancies",
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
    input) and ``confirm_tool`` (the matching tool name) so the "Confirm
    Receipt" button can re-invoke the tool directly with ``preview=False``
    and the request's values inlined (see #491). Both kwargs are optional
    because the same builder is reused for the non-preview render where
    no confirm button is shown — but they must be set together.
    """
    if (confirm_request is None) != (confirm_tool is None):
        raise ValueError(
            "confirm_request and confirm_tool must be set together (or both None)"
        )

    order_number = response.get("order_number", "N/A")
    is_preview = response.get("is_preview", True)
    state: dict[str, Any] = {"response": response, "result": None}
    confirm_action: CallTool | None = None
    if confirm_request is not None and confirm_tool is not None:
        confirm_action = _build_confirm_action(
            confirm_tool,
            confirm_request,
            success_message=f"Receipt for {order_number} recorded",
            success_chat=(
                f"Items received for {order_number}; inventory has been updated."
            ),
            error_message=f"Receipt for {order_number} failed",
            error_chat=(
                f"Receiving items for {order_number} failed — please review "
                "the error and try again."
            ),
        )

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
            if is_preview and confirm_action is not None:
                with Row(gap=2):
                    if not block_warnings:
                        Button(
                            label="Confirm Receipt",
                            variant="default",
                            on_click=confirm_action,
                        )
                    Button(
                        label="Cancel",
                        variant="outline",
                        on_click=ShowToast(message="Receipt cancelled", variant="info"),
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
    input) and ``confirm_tool`` (the matching tool name) so the "Execute
    batch" button can re-invoke the tool directly with ``preview=False``
    and the request's values inlined (see #491). Both kwargs are optional
    because the same builder is reused for the non-preview render — but
    they must be set together.
    """
    if (confirm_request is None) != (confirm_tool is None):
        raise ValueError(
            "confirm_request and confirm_tool must be set together (or both None)"
        )
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
        "result": None,
    }
    confirm_action: CallTool | None = None
    if confirm_request is not None and confirm_tool is not None:
        confirm_action = _build_confirm_action(
            confirm_tool,
            confirm_request,
            success_message=f"Batch executed: {total} ops",
            success_chat=(
                f"Batch recipe update executed: {total} planned operation(s) "
                "submitted. Review the results card for per-op success / "
                "failure / skip status."
            ),
            error_message="Batch execution failed",
            error_chat=(
                "Batch recipe update failed before completing — please "
                "review the error and re-run."
            ),
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
            rows="rows",
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
        with Row(gap=2):
            if is_preview and confirm_action is not None:
                Button(
                    label="Execute batch",
                    variant="default",
                    on_click=confirm_action,
                )
            elif failed > 0:
                Button(
                    label="Review failed ops",
                    variant="outline",
                    on_click=SendMessage(
                        "List the failed sub-operations from the last batch update "
                        "and suggest recovery steps"
                    ),
                )
            else:
                Button(
                    label="Verify recipes",
                    variant="outline",
                    on_click=SendMessage(
                        "Verify the updated manufacturing order recipes"
                    ),
                )

    return app
