from enum import StrEnum


class FindPurchaseOrdersExtendItem(StrEnum):
    SUPPLIER = "supplier"

    def __str__(self) -> str:
        return str(self.value)
