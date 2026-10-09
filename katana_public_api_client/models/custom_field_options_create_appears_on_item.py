from enum import StrEnum


class CustomFieldOptionsCreateAppearsOnItem(StrEnum):
    MANUFACTURINGORDER = "ManufacturingOrder"
    OUTSOURCEDPURCHASEORDERROW = "OutsourcedPurchaseOrderRow"
    PURCHASEORDERROW = "PurchaseOrderRow"
    SALESORDERROW = "SalesOrderRow"

    def __str__(self) -> str:
        return str(self.value)
