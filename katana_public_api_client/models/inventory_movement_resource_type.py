from enum import StrEnum


class InventoryMovementResourceType(StrEnum):
    MANUFACTURINGORDER = "ManufacturingOrder"
    MANUFACTURINGORDERRECIPEROW = "ManufacturingOrderRecipeRow"
    PRODUCTION = "Production"
    PRODUCTIONINGREDIENT = "ProductionIngredient"
    PURCHASEORDERRECIPEROW = "PurchaseOrderRecipeRow"
    PURCHASEORDERROW = "PurchaseOrderRow"
    SALESORDERROW = "SalesOrderRow"
    STOCKADJUSTMENTROW = "StockAdjustmentRow"
    STOCKTRANSFERROW = "StockTransferRow"
    SYSTEMGENERATED = "SystemGenerated"

    def __str__(self) -> str:
        return str(self.value)
