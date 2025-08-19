from enum import Enum


class GetAllSalesReturnsRefundStatus(str, Enum):
    NOT_REFUNDED = "NOT_REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    REFUNDED_ALL = "REFUNDED_ALL"

    def __str__(self) -> str:
        return str(self.value)
