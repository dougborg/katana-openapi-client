from enum import StrEnum


class SalesOrderStatus(StrEnum):
    DELIVERED = "DELIVERED"
    NOT_SHIPPED = "NOT_SHIPPED"
    PACKED = "PACKED"
    PARTIALLY_DELIVERED = "PARTIALLY_DELIVERED"
    PARTIALLY_PACKED = "PARTIALLY_PACKED"
    PENDING = "PENDING"
    READY_FOR_FULFILLMENT = "READY_FOR_FULFILLMENT"

    def __str__(self) -> str:
        return str(self.value)
