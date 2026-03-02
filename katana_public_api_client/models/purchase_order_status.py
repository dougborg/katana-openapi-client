from enum import StrEnum


class PurchaseOrderStatus(StrEnum):
    NOT_RECEIVED = "NOT_RECEIVED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"

    def __str__(self) -> str:
        return str(self.value)
