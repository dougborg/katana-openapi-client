from enum import StrEnum


class GetAllSalesReturnsRefundStatus(StrEnum):
    NOT_REFUNDED = "NOT_REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    REFUNDED_ALL = "REFUNDED_ALL"

    def __str__(self) -> str:
        return str(self.value)
