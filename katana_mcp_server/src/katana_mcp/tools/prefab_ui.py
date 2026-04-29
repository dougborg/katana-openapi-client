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


def call_tool_from_request(
    tool_name: str,
    request_model: type[BaseModel],
    *,
    state_key: str = "request",
    overrides: dict[str, Any] | None = None,
) -> CallTool:
    """Build a CallTool action that re-invokes ``tool_name`` with every field
    of ``request_model`` templated from iframe state.

    Each field on the Pydantic request model maps to a ``{{ <state_key>.field }}``
    template string. ``overrides`` (e.g. ``{"confirm": True}``) take precedence
    over the templated values — use them to flip a flag or substitute a literal.

    The caller must seed the iframe state with the original request under
    ``state_key`` (default ``"request"``); the matching builder
    (``build_order_preview_ui`` and friends) accepts a ``request=`` kwarg
    that does this.
    """
    valid_fields = set(request_model.model_fields)
    args: dict[str, Any] = {
        name: f"{{{{ {state_key}.{name} }}}}" for name in valid_fields
    }
    if overrides:
        bad = sorted(set(overrides) - valid_fields)
        if bad:
            raise ValueError(
                f"Invalid override field(s) for {request_model.__name__}: "
                f"{', '.join(bad)}"
            )
        args.update(overrides)
    return CallTool(tool_name, arguments=args)


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
    """Render shared order content fields (supplier/customer/location + total)."""
    if total is not None:
        Metric(label="Total", value=f"${total:,.2f} {currency}")
    if order.get("supplier_id"):
        Text(content=f"Supplier ID: {order['supplier_id']}")
    if order.get("customer_id"):
        Text(content=f"Customer ID: {order['customer_id']}")
    if order.get("location_id"):
        Text(content=f"Location ID: {order['location_id']}")


def build_order_preview_ui(
    order: dict[str, Any],
    order_type: OrderType,
    *,
    confirm_action: Action,
    request: dict[str, Any],
) -> PrefabApp:
    """Build an order preview card with confirm/cancel buttons.

    Caller supplies ``confirm_action`` (typically a ``CallTool`` built via
    ``call_tool_from_request``) so each tool (sales/PO/MO) wires its own
    direct re-invocation with ``confirm=True``. ``request`` is the original
    input dict (``request.model_dump()``); it's seeded into iframe state at
    ``state.request`` so ``CallTool``'s ``{{ request.* }}`` templates
    resolve.
    """
    fields = _extract_order_fields(order)
    state: dict[str, Any] = {"order": order, "request": request}

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

            if order.get("warnings"):
                Separator()
                for warning in order["warnings"]:
                    Badge(label=warning, variant="destructive")

        with CardFooter():
            Muted(content="This is a preview. No changes have been made.")

            with Row(gap=2):
                Button(
                    label="Confirm & Create",
                    variant="default",
                    on_click=confirm_action,
                )
                Button(
                    label="Cancel",
                    variant="outline",
                    on_click=SendMessage(f"Cancel the {order_type.lower()} creation"),
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
    ``CallTool`` with ``confirm=True`` and the original order_id/order_type
    sourced from the response (where they're echoed). No LLM round-trip.
    """
    order_type, order_number, status = _extract_fulfill_fields(response)

    with PrefabApp(state={"response": response}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Fulfill {order_type} Order")
            Badge(label=order_number, variant="outline")
            Badge(label=status, variant="secondary")

        with CardContent(), Column(gap=2):
            _render_inventory_updates(response)

            if response.get("warnings"):
                Separator()
                for warning in response["warnings"]:
                    Badge(label=warning, variant="destructive")

        with CardFooter(), Row(gap=2):
            Button(
                label="Confirm Fulfillment",
                variant="default",
                on_click=CallTool(
                    "fulfill_order",
                    arguments={
                        "order_id": "{{ response.order_id }}",
                        "order_type": "{{ response.order_type }}",
                        "confirm": True,
                    },
                ),
            )
            Button(
                label="Cancel",
                variant="outline",
                on_click=SendMessage("Cancel the fulfillment"),
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
    request: dict[str, Any] | None = None,
    confirm_action: Action | None = None,
) -> PrefabApp:
    """Build a receipt card for received purchase order items.

    On the preview branch the caller must supply both ``request`` (seeded
    into iframe state at ``state.request``) and ``confirm_action`` (a
    ``CallTool`` built via ``call_tool_from_request``) so the "Confirm
    Receipt" button can re-invoke ``receive_purchase_order`` directly with
    ``confirm=True``. Both kwargs are optional because the same builder is
    reused for the non-preview render where no confirm button is shown.
    """
    order_number = response.get("order_number", "N/A")
    is_preview = response.get("is_preview", True)
    state: dict[str, Any] = {"response": response}
    if request is not None:
        state["request"] = request

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

        with CardFooter():
            if is_preview and confirm_action is not None:
                with Row(gap=2):
                    Button(
                        label="Confirm Receipt",
                        variant="default",
                        on_click=confirm_action,
                    )
                    Button(
                        label="Cancel",
                        variant="outline",
                        on_click=SendMessage("Cancel the receipt"),
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
    request: dict[str, Any] | None = None,
    confirm_action: Action | None = None,
) -> PrefabApp:
    """Build a batch recipe update card with per-group tables and summary metrics.

    Shows one row per planned sub-op grouped by replacement group_label.
    Preview mode shows all ops as PENDING; executed mode shows SUCCESS/FAILED/SKIPPED.

    On the preview branch, the "Execute batch" button uses ``confirm_action``
    (typically a ``CallTool`` built from the original request via
    ``call_tool_from_request``) for direct re-invocation with ``confirm=True``.
    Pass ``request=request.model_dump()`` from the caller so the iframe state
    has the original input under ``state.request``.
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
    }
    if request is not None:
        state["request"] = request

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
