"""Prefab UI builders for Katana MCP Server tool responses.

Provides reusable Prefab component builders that produce rich interactive UIs
for Claude Desktop (via structuredContent), while tools continue to serve
markdown fallback via templates for non-Prefab MCP clients.

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
    return make_tool_result(
        response, "item_search_results", ui=app, **template_vars
    )
"""

from __future__ import annotations

from typing import Any, Literal

from prefab_ui.actions import SetState, ShowToast
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
            H3("Search Results")
            Badge(f"Query: {query}", variant="outline")
            Badge(f"{total_count} items", variant="secondary")

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
            page_size=20,
            on_row_click=CallTool(
                "get_variant_details",
                arguments={"sku": "{{ sku }}"},
                on_success=SetState("detail", RESULT),
                on_error=ShowToast("{{ $error }}", variant="error"),
            ),
        )

        with Slot("detail"):
            Muted("Click a row to see variant details")

        with Row(gap=2):
            Button(
                "Check inventory for search results",
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
            CardTitle(variant.get("name", "Unknown"))
            Badge(variant.get("sku", ""), variant="outline")
            if variant.get("type"):
                Badge(
                    variant["type"],
                    variant="secondary",
                )

        with CardContent(), Column(gap=3):
            with Row(gap=4):
                Metric(
                    "Sales Price",
                    f"${variant.get('sales_price', 0):,.2f}"
                    if variant.get("sales_price") is not None
                    else "N/A",
                )
                Metric(
                    "Purchase Price",
                    f"${variant.get('purchase_price', 0):,.2f}"
                    if variant.get("purchase_price") is not None
                    else "N/A",
                )

            Separator()

            with Row(gap=4):
                Text(f"ID: {variant.get('id', 'N/A')}")
                if variant.get("product_id"):
                    Text(f"Product ID: {variant['product_id']}")
                if variant.get("material_id"):
                    Text(f"Material ID: {variant['material_id']}")
                if variant.get("lead_time") is not None:
                    Text(f"Lead Time: {variant['lead_time']} days")

            if variant.get("supplier_item_codes"):
                Muted("Supplier Codes:")
                with ForEach("variant.supplier_item_codes"):
                    Text("{{ $item }}")

        with CardFooter(), Row(gap=2):
            Button(
                "Check Inventory",
                variant="outline",
                on_click=SendMessage(
                    f"Check inventory for SKU {variant.get('sku', '')}"
                ),
            )
            Button(
                "Create Purchase Order",
                variant="outline",
                on_click=SendMessage(
                    f"Create a purchase order for SKU {variant.get('sku', '')}"
                ),
            )
    return app


def build_item_detail_ui(
    item: dict[str, Any],
) -> PrefabApp:
    """Build a detail card for an item (product/material/service)."""
    with PrefabApp(state={"item": item}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(item.get("name", "Unknown"))
            Badge(item.get("type", ""), variant="secondary")

        with CardContent(), Column(gap=2):
            Text(f"ID: {item.get('id', 'N/A')}")
            if item.get("uom"):
                Text(f"Unit of Measure: {item['uom']}")
            if item.get("category_name"):
                Text(f"Category: {item['category_name']}")

            with Row(gap=2):
                if item.get("is_sellable") is not None:
                    Badge(
                        "Sellable" if item["is_sellable"] else "Not Sellable",
                        variant="default" if item["is_sellable"] else "secondary",
                    )
                if item.get("is_producible") is not None:
                    Badge(
                        "Producible" if item["is_producible"] else "Not Producible",
                        variant="default" if item["is_producible"] else "secondary",
                    )

        with CardFooter():
            Button(
                "Get Variant Details",
                variant="outline",
                on_click=SendMessage(
                    f"Get variant details for item ID {item.get('id', '')}"
                ),
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
            CardTitle(stock.get("product_name", "Unknown"))
            Badge(stock.get("sku", ""), variant="outline")

        with CardContent(), Row(gap=4):
            Metric("Available", str(stock.get("available_stock", 0)))
            Metric("Committed", str(stock.get("committed", 0)))
            Metric("In Production", str(stock.get("in_production", 0)))

        with CardFooter(), Row(gap=2):
            Button(
                "Reorder",
                variant="outline",
                on_click=SendMessage(
                    f"Create a purchase order to reorder SKU {stock.get('sku', '')}"
                ),
            )
            Button(
                "View Low Stock",
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
            H3("Low Stock Report")
            Badge(f"Threshold: {threshold}", variant="outline")
            Badge(
                f"{total_count} items",
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
            "Create Restock Orders",
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
        Metric("Total", f"${total:,.2f} {currency}")
    if order.get("supplier_id"):
        Text(f"Supplier ID: {order['supplier_id']}")
    if order.get("customer_id"):
        Text(f"Customer ID: {order['customer_id']}")
    if order.get("location_id"):
        Text(f"Location ID: {order['location_id']}")


def build_order_preview_ui(
    order: dict[str, Any],
    order_type: OrderType,
) -> PrefabApp:
    """Build an order preview card with confirm/cancel buttons."""
    fields = _extract_order_fields(order)

    with PrefabApp(state={"order": order}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(f"{order_type} Preview")
            Badge(fields["order_number"], variant="outline")
            Badge("PREVIEW", variant="secondary")

        with CardContent(), Column(gap=3):
            _render_order_fields(
                order, total=fields["total"], currency=fields["currency"]
            )
            if order.get("variant_id"):
                Text(f"Variant ID: {order['variant_id']}")
            if order.get("planned_quantity"):
                Text(f"Planned Quantity: {order['planned_quantity']}")

            if order.get("warnings"):
                Separator()
                for warning in order["warnings"]:
                    Badge(warning, variant="destructive")

        with CardFooter():
            Muted("This is a preview. No changes have been made.")

            with Row(gap=2):
                Button(
                    "Confirm & Create",
                    variant="default",
                    on_click=SendMessage(
                        f"Create the {order_type.lower()} with confirm=true"
                    ),
                )
                Button(
                    "Cancel",
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
            CardTitle(f"{order_type} Created")
            Badge(fields["order_number"], variant="outline")
            Badge(fields["status"], variant="default")

        with CardContent(), Column(gap=2):
            Text(f"Order ID: {order_id}")
            _render_order_fields(
                order, total=fields["total"], currency=fields["currency"]
            )

        with CardFooter(), Row(gap=2):
            if order_type == "Purchase Order":
                Button(
                    "Receive Items",
                    variant="outline",
                    on_click=SendMessage(
                        f"Receive items for purchase order {order_id}"
                    ),
                )
                Button(
                    "Verify Document",
                    variant="outline",
                    on_click=SendMessage(
                        f"Verify a supplier document against PO {order_id}"
                    ),
                )
            elif order_type == "Sales Order":
                Button(
                    "Fulfill Order",
                    variant="outline",
                    on_click=SendMessage(f"Fulfill sales order {order_id}"),
                )
            elif order_type == "Manufacturing Order":
                Button(
                    "Complete Order",
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
        Muted(label)
        for update in response["inventory_updates"]:
            Text(f"  {update}")


def build_fulfill_preview_ui(
    response: dict[str, Any],
) -> PrefabApp:
    """Build a fulfillment preview card."""
    order_type, order_number, status = _extract_fulfill_fields(response)

    with PrefabApp(state={"response": response}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(f"Fulfill {order_type} Order")
            Badge(order_number, variant="outline")
            Badge(status, variant="secondary")

        with CardContent(), Column(gap=2):
            _render_inventory_updates(response)

            if response.get("warnings"):
                Separator()
                for warning in response["warnings"]:
                    Badge(warning, variant="destructive")

        with CardFooter(), Row(gap=2):
            Button(
                "Confirm Fulfillment",
                variant="default",
                on_click=SendMessage(
                    f"Fulfill the {response.get('order_type', '')} order "
                    f"{response.get('order_id', '')} with confirm=true"
                ),
            )
            Button(
                "Cancel",
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
            CardTitle(f"{order_type} Order Fulfilled")
            Badge(order_number, variant="outline")
            Badge(status, variant="default")

        with CardContent(), Column(gap=2):
            if response.get("message"):
                Text(response["message"])
            if response.get("inventory_updates"):
                Separator()
            _render_inventory_updates(response, label="Inventory Updates:")

        with CardFooter():
            Button(
                "Check Inventory",
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
            H3("Document Verification")
            Badge(f"PO {response.get('order_id', 'N/A')}", variant="outline")
            Badge(overall_status.replace("_", " ").title(), variant=status_variant)

        # Matches table
        if matches:
            Muted("Matched Items:")
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
            Muted("Discrepancies:")
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
                    "Proceed to Receive",
                    variant="default",
                    on_click=SendMessage(
                        f"Receive items for purchase order {response.get('order_id', '')}"
                    ),
                )
            else:
                Button(
                    "Receive Anyway",
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
            CardTitle(f"Item {action}")
            if item.get("type"):
                Badge(str(item["type"]), variant="secondary")

        with CardContent(), Column(gap=2):
            Text(f"ID: {item.get('id', 'N/A')}")
            Text(f"Name: {item.get('name', 'N/A')}")
            if item.get("sku"):
                Text(f"SKU: {item['sku']}")
            if item.get("message"):
                Text(item["message"])

        with CardFooter(), Row(gap=2):
            if item.get("sku"):
                Button(
                    "View Details",
                    variant="outline",
                    on_click=SendMessage(f"Get variant details for SKU {item['sku']}"),
                )
            Button(
                "Check Inventory",
                variant="outline",
                on_click=SendMessage(
                    f"Check inventory for item ID {item.get('id', '')}"
                ),
            )
    return app


# ============================================================================
# Receipt UI
# ============================================================================


def build_receipt_ui(
    response: dict[str, Any],
) -> PrefabApp:
    """Build a receipt card for received purchase order items."""
    order_number = response.get("order_number", "N/A")
    is_preview = response.get("is_preview", True)

    with PrefabApp(state={"response": response}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle("Purchase Order Receipt")
            Badge(order_number, variant="outline")
            Badge(
                "PREVIEW" if is_preview else "RECEIVED",
                variant="secondary" if is_preview else "default",
            )

        with CardContent(), Column(gap=2):
            if response.get("message"):
                Text(response["message"])
            Metric(
                "Items Received",
                str(response.get("items_received", 0)),
            )

        with CardFooter():
            if is_preview:
                with Row(gap=2):
                    Button(
                        "Confirm Receipt",
                        variant="default",
                        on_click=SendMessage(
                            f"Receive items for PO {response.get('order_id', '')} "
                            "with confirm=true"
                        ),
                    )
                    Button(
                        "Cancel",
                        variant="outline",
                        on_click=SendMessage("Cancel the receipt"),
                    )
            else:
                Button(
                    "Check Inventory",
                    variant="outline",
                    on_click=SendMessage(
                        "Check current inventory levels after receipt"
                    ),
                )
    return app
