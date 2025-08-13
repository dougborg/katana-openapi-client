from enum import Enum


class WebhookEvent(str, Enum):
    CURRENT_INVENTORY_MATERIAL_OUT_OF_STOCK = "current_inventory.material_out_of_stock"
    CURRENT_INVENTORY_MATERIAL_UPDATED = "current_inventory.material_updated"
    CURRENT_INVENTORY_PRODUCT_OUT_OF_STOCK = "current_inventory.product_out_of_stock"
    CURRENT_INVENTORY_PRODUCT_UPDATED = "current_inventory.product_updated"
    MANUFACTURING_ORDER_BLOCKED = "manufacturing_order.blocked"
    MANUFACTURING_ORDER_CREATED = "manufacturing_order.created"
    MANUFACTURING_ORDER_DELETED = "manufacturing_order.deleted"
    MANUFACTURING_ORDER_DONE = "manufacturing_order.done"
    MANUFACTURING_ORDER_IN_PROGRESS = "manufacturing_order.in_progress"
    MANUFACTURING_ORDER_OPERATION_ROW_BLOCKED = (
        "manufacturing_order_operation_row.blocked"
    )
    MANUFACTURING_ORDER_OPERATION_ROW_COMPLETED = (
        "manufacturing_order_operation_row.completed"
    )
    MANUFACTURING_ORDER_OPERATION_ROW_CREATED = (
        "manufacturing_order_operation_row.created"
    )
    MANUFACTURING_ORDER_OPERATION_ROW_DELETED = (
        "manufacturing_order_operation_row.deleted"
    )
    MANUFACTURING_ORDER_OPERATION_ROW_IN_PROGRESS = (
        "manufacturing_order_operation_row.in_progress"
    )
    MANUFACTURING_ORDER_OPERATION_ROW_PAUSED = (
        "manufacturing_order_operation_row.paused"
    )
    MANUFACTURING_ORDER_OPERATION_ROW_UPDATED = (
        "manufacturing_order_operation_row.updated"
    )
    MANUFACTURING_ORDER_RECIPE_ROW_CREATED = "manufacturing_order_recipe_row.created"
    MANUFACTURING_ORDER_RECIPE_ROW_DELETED = "manufacturing_order_recipe_row.deleted"
    MANUFACTURING_ORDER_RECIPE_ROW_INGREDIENTS_IN_STOCK = (
        "manufacturing_order_recipe_row.ingredients_in_stock"
    )
    MANUFACTURING_ORDER_RECIPE_ROW_UPDATED = "manufacturing_order_recipe_row.updated"
    MANUFACTURING_ORDER_UPDATED = "manufacturing_order.updated"
    MATERIAL_CREATED = "material.created"
    MATERIAL_DELETED = "material.deleted"
    MATERIAL_UPDATED = "material.updated"
    OUTSOURCED_PURCHASE_ORDER_CREATED = "outsourced_purchase_order.created"
    OUTSOURCED_PURCHASE_ORDER_DELETED = "outsourced_purchase_order.deleted"
    OUTSOURCED_PURCHASE_ORDER_RECEIVED = "outsourced_purchase_order.received"
    OUTSOURCED_PURCHASE_ORDER_RECIPE_ROW_CREATED = (
        "outsourced_purchase_order_recipe_row.created"
    )
    OUTSOURCED_PURCHASE_ORDER_RECIPE_ROW_DELETED = (
        "outsourced_purchase_order_recipe_row.deleted"
    )
    OUTSOURCED_PURCHASE_ORDER_RECIPE_ROW_UPDATED = (
        "outsourced_purchase_order_recipe_row.updated"
    )
    OUTSOURCED_PURCHASE_ORDER_ROW_CREATED = "outsourced_purchase_order_row.created"
    OUTSOURCED_PURCHASE_ORDER_ROW_DELETED = "outsourced_purchase_order_row.deleted"
    OUTSOURCED_PURCHASE_ORDER_ROW_RECEIVED = "outsourced_purchase_order_row.received"
    OUTSOURCED_PURCHASE_ORDER_ROW_UPDATED = "outsourced_purchase_order_row.updated"
    OUTSOURCED_PURCHASE_ORDER_UPDATED = "outsourced_purchase_order.updated"
    PRODUCT_CREATED = "product.created"
    PRODUCT_DELETED = "product.deleted"
    PRODUCT_RECIPE_ROW_CREATED = "product_recipe_row.created"
    PRODUCT_RECIPE_ROW_DELETED = "product_recipe_row.deleted"
    PRODUCT_RECIPE_ROW_UPDATED = "product_recipe_row.updated"
    PRODUCT_UPDATED = "product.updated"
    PURCHASE_ORDER_CREATED = "purchase_order.created"
    PURCHASE_ORDER_DELETED = "purchase_order.deleted"
    PURCHASE_ORDER_PARTIALLY_RECEIVED = "purchase_order.partially_received"
    PURCHASE_ORDER_RECEIVED = "purchase_order.received"
    PURCHASE_ORDER_ROW_CREATED = "purchase_order_row.created"
    PURCHASE_ORDER_ROW_DELETED = "purchase_order_row.deleted"
    PURCHASE_ORDER_ROW_RECEIVED = "purchase_order_row.received"
    PURCHASE_ORDER_ROW_UPDATED = "purchase_order_row.updated"
    PURCHASE_ORDER_UPDATED = "purchase_order.updated"
    SALES_ORDER_AVAILABILITY_UPDATED = "sales_order.availability_updated"
    SALES_ORDER_CREATED = "sales_order.created"
    SALES_ORDER_DELETED = "sales_order.deleted"
    SALES_ORDER_DELIVERED = "sales_order.delivered"
    SALES_ORDER_PACKED = "sales_order.packed"
    SALES_ORDER_UPDATED = "sales_order.updated"
    VARIANT_CREATED = "variant.created"
    VARIANT_DELETED = "variant.deleted"
    VARIANT_UPDATED = "variant.updated"

    def __str__(self) -> str:
        return str(self.value)
