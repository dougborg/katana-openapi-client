"""Data-driven registry mapping accessor names to generated API modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResourceConfig:
    """Maps a logical resource to its generated API module functions.

    Attributes:
        module: Directory name under ``api/`` (e.g. ``"product"``).
        get_one: Module name for single-resource GET, or ``None``.
        get_all: Module name for list GET, or ``None``.
        create: Module name for POST, or ``None``.
        update: Module name for PATCH/PUT, or ``None``.
        delete: Module name for DELETE, or ``None``.
    """

    module: str
    get_one: str | None = None
    get_all: str | None = None
    create: str | None = None
    update: str | None = None
    delete: str | None = None


RESOURCE_REGISTRY: dict[str, ResourceConfig] = {
    # ── Full CRUD (get, list, create, update, delete) ────────────────────
    "products": ResourceConfig(
        "product",
        "get_product",
        "get_all_products",
        "create_product",
        "update_product",
        "delete_product",
    ),
    "variants": ResourceConfig(
        "variant",
        "get_variant",
        "get_all_variants",
        "create_variant",
        "update_variant",
        "delete_variant",
    ),
    "materials": ResourceConfig(
        "material",
        "get_material",
        "get_all_materials",
        "create_material",
        "update_material",
        "delete_material",
    ),
    "services": ResourceConfig(
        "services",
        "get_service",
        "get_all_services",
        "create_service",
        "update_service",
        "delete_service",
    ),
    "price_lists": ResourceConfig(
        "price_list",
        "get_price_list",
        "get_all_price_lists",
        "create_price_list",
        "update_price_list",
        "delete_price_list",
    ),
    "price_list_customers": ResourceConfig(
        "price_list_customer",
        "get_price_list_customer",
        "get_all_price_list_customers",
        "create_price_list_customer",
        "update_price_list_customer",
        "delete_price_list_customer",
    ),
    "price_list_rows": ResourceConfig(
        "price_list_row",
        "get_price_list_row",
        "get_all_price_list_rows",
        "create_price_list_row",
        "update_price_list_row",
        "delete_price_list_row",
    ),
    "sales_orders": ResourceConfig(
        "sales_order",
        "get_sales_order",
        "get_all_sales_orders",
        "create_sales_order",
        "update_sales_order",
        "delete_sales_order",
    ),
    "sales_order_fulfillments": ResourceConfig(
        "sales_order_fulfillment",
        "get_sales_order_fulfillment",
        "get_all_sales_order_fulfillments",
        "create_sales_order_fulfillment",
        "update_sales_order_fulfillment",
        "delete_sales_order_fulfillment",
    ),
    "sales_order_rows": ResourceConfig(
        "sales_order_row",
        "get_sales_order_row",
        "get_all_sales_order_rows",
        "create_sales_order_row",
        "update_sales_order_row",
        "delete_sales_order_row",
    ),
    "sales_returns": ResourceConfig(
        "sales_return",
        "get_sales_return",
        "get_all_sales_returns",
        "create_sales_return",
        "update_sales_return",
        "delete_sales_return",
    ),
    "sales_return_rows": ResourceConfig(
        "sales_return_row",
        "get_sales_return_row",
        "get_all_sales_return_rows",
        "create_sales_return_row",
        "update_sales_return_row",
        "delete_sales_return_row",
    ),
    "manufacturing_orders": ResourceConfig(
        "manufacturing_order",
        "get_manufacturing_order",
        "get_all_manufacturing_orders",
        "create_manufacturing_order",
        "update_manufacturing_order",
        "delete_manufacturing_order",
    ),
    "manufacturing_order_operations": ResourceConfig(
        "manufacturing_order_operation",
        "get_manufacturing_order_operation_row",
        "get_all_manufacturing_order_operation_rows",
        "create_manufacturing_order_operation_row",
        "update_manufacturing_order_operation_row",
        "delete_manufacturing_order_operation_row",
    ),
    "manufacturing_order_recipes": ResourceConfig(
        "manufacturing_order_recipe",
        "get_manufacturing_order_recipe_row",
        "get_all_manufacturing_order_recipe_rows",
        "create_manufacturing_order_recipe_rows",
        "update_manufacturing_order_recipe_rows",
        "delete_manufacturing_order_recipe_row",
    ),
    "manufacturing_order_productions": ResourceConfig(
        "manufacturing_order_production",
        "get_manufacturing_order_production",
        None,
        "create_manufacturing_order_production",
        "update_manufacturing_order_production",
        "delete_manufacturing_order_production",
    ),
    "webhooks": ResourceConfig(
        "webhook",
        "get_webhook",
        "get_all_webhooks",
        "create_webhook",
        "update_webhook",
        "delete_webhook",
    ),
    "purchase_orders": ResourceConfig(
        "purchase_order",
        "get_purchase_order",
        "find_purchase_orders",
        "create_purchase_order",
        "update_purchase_order",
        "delete_purchase_order",
    ),
    "purchase_order_rows": ResourceConfig(
        "purchase_order_row",
        "get_purchase_order_row",
        "get_all_purchase_order_rows",
        "create_purchase_order_row",
        "update_purchase_order_row",
        "delete_purchase_order_row",
    ),
    "purchase_order_additional_cost_rows": ResourceConfig(
        "purchase_order_additional_cost_row",
        "get_po_additional_cost_row",
        "get_purchase_order_additional_cost_rows",
        "create_po_additional_cost_row",
        "update_additional_cost_row",
        "delete_po_additional_cost",
    ),
    # ── CRUD without get-one ─────────────────────────────────────────────
    "customers": ResourceConfig(
        "customer",
        None,
        "get_all_customers",
        "create_customer",
        "update_customer",
        "delete_customer",
    ),
    "customer_addresses": ResourceConfig(
        "customer_address",
        None,
        "get_all_customer_addresses",
        "create_customer_address",
        "update_customer_address",
        "delete_customer_address",
    ),
    "suppliers": ResourceConfig(
        "supplier",
        None,
        "get_all_suppliers",
        "create_supplier",
        "update_supplier",
        "delete_supplier",
    ),
    "supplier_addresses": ResourceConfig(
        "supplier_address",
        None,
        "get_supplier_addresses",
        "create_supplier_address",
        "update_supplier_address",
        "delete_supplier_address",
    ),
    "sales_order_addresses": ResourceConfig(
        "sales_order_address",
        None,
        "get_all_sales_order_addresses",
        "create_sales_order_address",
        "update_sales_order_address",
        "delete_sales_order_address",
    ),
    "bom_rows": ResourceConfig(
        "bom_row",
        None,
        "get_all_bom_rows",
        "create_bom_row",
        "update_bom_row",
        "delete_bom_row",
    ),
    "stocktakes": ResourceConfig(
        "stocktake",
        None,
        "get_all_stocktakes",
        "create_stocktake",
        "update_stocktake",
        "delete_stocktake",
    ),
    "stocktake_rows": ResourceConfig(
        "stocktake_row",
        None,
        "get_all_stocktake_rows",
        "create_stocktake_row",
        "update_stocktake_row",
        "delete_stocktake_row",
    ),
    "stock_adjustments": ResourceConfig(
        "stock_adjustment",
        None,
        "get_all_stock_adjustments",
        "create_stock_adjustment",
        "update_stock_adjustment",
        "delete_stock_adjustment",
    ),
    "stock_transfers": ResourceConfig(
        "stock_transfer",
        None,
        "get_all_stock_transfers",
        "create_stock_transfer",
        "update_stock_transfer",
        "delete_stock_transfer",
    ),
    # ── Sub-resources in "plural" API directories ────────────────────────
    "product_operation_rows": ResourceConfig(
        "products",
        None,
        "get_all_product_operation_rows",
        "create_product_operation_rows",
        "update_product_operation_row",
        "delete_product_operation_row",
    ),
    "outsourced_po_recipe_rows": ResourceConfig(
        "purchase_orders",
        "get_outsourced_purchase_order_recipe_row",
        "get_outsourced_purchase_order_recipe_rows",
        "create_outsourced_purchase_order_recipe_row",
        "update_outsourced_purchase_order_recipe_row",
        "delete_outsourced_purchase_order_recipe_row",
    ),
    "sales_order_shipping_fees": ResourceConfig(
        "sales_orders",
        "get_sales_order_shipping_fee",
        "get_sales_order_shipping_fees",
        "create_sales_order_shipping_fee",
        "update_sales_order_shipping_fee",
        "delete_sales_order_shipping_fee",
    ),
    # ── Partial / non-standard CRUD ──────────────────────────────────────
    "recipes": ResourceConfig(
        "recipe",
        None,
        "get_all_recipes",
        "create_recipes",
        "update_recipe_row",
        "delete_recipe_row",
    ),
    "serial_numbers": ResourceConfig(
        "serial_number",
        None,
        "get_all_serial_numbers",
        "create_serial_numbers",
    ),
    "batches": ResourceConfig(
        "batch",
        None,
        "get_batch_stock",
        "create_batch",
        "update_batch_stock",
    ),
    "demand_forecasts": ResourceConfig(
        "demand_forecast",
        None,
        "get_demand_forecasts",
        "create_demand_forecast",
    ),
    "storage_bins": ResourceConfig(
        "storage_bin",
        None,
        "get_all_storage_bins",
        None,
        None,
        "delete_storage_bin",
    ),
    "tax_rates": ResourceConfig(
        "tax_rate",
        None,
        "get_all_tax_rates",
        "create_tax_rate",
    ),
    # ── Read-only resources ──────────────────────────────────────────────
    "additional_costs": ResourceConfig(
        "additional_costs",
        None,
        "get_additional_costs",
    ),
    "custom_fields": ResourceConfig(
        "custom_fields",
        None,
        "get_all_custom_fields_collections",
    ),
    # factory excluded: singleton endpoint (no ID param), use Layer 1 directly
    "inventory": ResourceConfig(
        "inventory",
        None,
        "get_all_inventory_point",
    ),
    "inventory_movements": ResourceConfig(
        "inventory_movements",
        None,
        "get_all_inventory_movements",
    ),
    "locations": ResourceConfig(
        "location",
        "get_location",
        "get_all_locations",
    ),
    "operators": ResourceConfig(
        "operator",
        None,
        "get_all_operators",
    ),
    "purchase_order_accounting_metadata": ResourceConfig(
        "purchase_order_accounting_metadata",
        None,
        "get_all_purchase_order_accounting_metadata",
    ),
    "sales_order_accounting_metadata": ResourceConfig(
        "sales_orders",
        None,
        "get_sales_order_accounting_metadata",
    ),
    "serial_number_stock": ResourceConfig(
        "serial_number",
        None,
        "get_all_serial_numbers_stock",
    ),
    "negative_stock": ResourceConfig(
        "inventory",
        None,
        "get_all_negative_stock",
    ),
    "users": ResourceConfig(
        "user",
        None,
        "get_all_users",
    ),
}
