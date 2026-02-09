from enum import StrEnum


class SerialNumberResourceType(StrEnum):
    MANUFACTURINGORDER = "ManufacturingOrder"
    PRODUCTION = "Production"
    PURCHASEORDERROW = "PurchaseOrderRow"
    SALESORDERFULFILLMENTROW = "SalesOrderFulfillmentRow"
    SALESORDERROW = "SalesOrderRow"
    STOCKADJUSTMENTROW = "StockAdjustmentRow"
    STOCKTRANSFERROW = "StockTransferRow"

    def __str__(self) -> str:
        return str(self.value)
