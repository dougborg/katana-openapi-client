from enum import StrEnum


class GetPurchaseOrderExtendItem(StrEnum):
    SUPPLIER = "supplier"

    def __str__(self) -> str:
        return str(self.value)
