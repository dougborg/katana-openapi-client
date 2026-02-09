from enum import StrEnum


class GetAllSerialNumbersResourceType(StrEnum):
    MANUFACTURINGORDER = "ManufacturingOrder"
    MANUFACTURINGORDERRECIPEROW = "ManufacturingOrderRecipeRow"
    PRODUCTIONINGREDIENT = "ProductionIngredient"
    PURCHASEORDERRECIPEROW = "PurchaseOrderRecipeRow"
    PURCHASEORDERROW = "PurchaseOrderRow"
    SALESORDERROW = "SalesOrderRow"
    STOCKADJUSTMENTROW = "StockAdjustmentRow"
    STOCKTRANSFERROW = "StockTransferRow"
    SYSTEMGENERATED = "SystemGenerated"

    def __str__(self) -> str:
        return str(self.value)
