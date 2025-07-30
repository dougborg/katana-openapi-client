from enum import Enum


class GetAllSerialNumbersResourceType(str, Enum):
    MANUFACTURINGORDER = "ManufacturingOrder"
    PRODUCTION = "Production"
    PURCHASEORDERROW = "PurchaseOrderRow"
    SALESORDERROW = "SalesOrderRow"
    STOCKADJUSTMENTROW = "StockAdjustmentRow"
    STOCKTRANSFERROW = "StockTransferRow"

    def __str__(self) -> str:
        return str(self.value)
