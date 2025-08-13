from enum import Enum


class GetAllInventoryMovementsResourceType(str, Enum):
    MANUFACTURINGORDER = "ManufacturingOrder"
    MANUFACTURINGORDERRECIPEROW = "ManufacturingOrderRecipeRow"
    PURCHASEORDERRECIPEROW = "PurchaseOrderRecipeRow"
    PURCHASEORDERROW = "PurchaseOrderRow"
    SALESORDERROW = "SalesOrderRow"
    STOCKADJUSTMENTROW = "StockAdjustmentRow"
    STOCKTRANSFERROW = "StockTransferRow"
    SYSTEMGENERATED = "SystemGenerated"

    def __str__(self) -> str:
        return str(self.value)
