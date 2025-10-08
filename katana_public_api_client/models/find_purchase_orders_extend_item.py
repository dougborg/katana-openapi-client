from enum import Enum


class FindPurchaseOrdersExtendItem(str, Enum):
    SUPPLIER = "supplier"

    def __str__(self) -> str:
        return str(self.value)
