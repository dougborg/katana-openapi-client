from enum import StrEnum


class SalesReturnRefundStatus(StrEnum):
    NOT_REFUNDED = "NOT_REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    REFUNDED = "REFUNDED"

    def __str__(self) -> str:
        return str(self.value)
