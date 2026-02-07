from enum import Enum


class CreateSerialNumbersRequestResourceType(str, Enum):
    MANUFACTURINGORDER = "ManufacturingOrder"
    PRODUCTION = "Production"
    PURCHASEORDERROW = "PurchaseOrderRow"
    SALESORDERROW = "SalesOrderRow"
    STOCKADJUSTMENTROW = "StockAdjustmentRow"
    STOCKTRANSFERROW = "StockTransferRow"

    def __str__(self) -> str:
        return str(self.value)
