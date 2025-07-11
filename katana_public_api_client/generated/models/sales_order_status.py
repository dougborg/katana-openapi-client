from enum import Enum


class SalesOrderStatus(str, Enum):
    DELIVERED = "DELIVERED"
    NOT_SHIPPED = "NOT_SHIPPED"
    PACKED = "PACKED"
    PARTIALLY_DELIVERED = "PARTIALLY_DELIVERED"
    PARTIALLY_PACKED = "PARTIALLY_PACKED"
    PENDING = "PENDING"

    def __str__(self) -> str:
        return str(self.value)
