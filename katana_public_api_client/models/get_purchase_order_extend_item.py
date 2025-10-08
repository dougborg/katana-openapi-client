from enum import Enum


class GetPurchaseOrderExtendItem(str, Enum):
    SUPPLIER = "supplier"

    def __str__(self) -> str:
        return str(self.value)
