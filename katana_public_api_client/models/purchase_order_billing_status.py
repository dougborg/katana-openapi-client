from enum import StrEnum


class PurchaseOrderBillingStatus(StrEnum):
    BILLED = "BILLED"
    NOT_BILLED = "NOT_BILLED"
    PARTIALLY_BILLED = "PARTIALLY_BILLED"

    def __str__(self) -> str:
        return str(self.value)
