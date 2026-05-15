from enum import StrEnum


class CustomFieldEntityType(StrEnum):
    CUSTOMER = "Customer"
    MANUFACTURINGORDER = "ManufacturingOrder"
    MANUFACTURINGORDERRECIPEROW = "ManufacturingOrderRecipeRow"
    MATERIALVARIANT = "MaterialVariant"
    OUTSOURCEDPURCHASEORDERROW = "OutsourcedPurchaseOrderRow"
    PRODUCTION = "Production"
    PRODUCTIONINGREDIENT = "ProductionIngredient"
    PRODUCTVARIANT = "ProductVariant"
    PURCHASEORDER = "PurchaseOrder"
    PURCHASEORDERRECIPEROW = "PurchaseOrderRecipeRow"
    PURCHASEORDERROW = "PurchaseOrderRow"
    SALESORDER = "SalesOrder"
    SALESORDERFULFILLMENTROW = "SalesOrderFulfillmentRow"
    SALESORDERROW = "SalesOrderRow"
    SALESRECIPEROW = "SalesRecipeRow"
    SERVICEVARIANT = "ServiceVariant"
    STOCKADJUSTMENT = "StockAdjustment"
    STOCKADJUSTMENTROW = "StockAdjustmentRow"
    STOCKTRANSFERROW = "StockTransferRow"

    def __str__(self) -> str:
        return str(self.value)
