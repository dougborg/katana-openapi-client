from enum import Enum


class FindPurchaseOrdersBillingStatus(str, Enum):
    BILLED = "BILLED"
    NOT_BILLED = "NOT_BILLED"
    PARTIALLY_BILLED = "PARTIALLY_BILLED"

    def __str__(self) -> str:
        return str(self.value)
