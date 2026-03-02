from enum import StrEnum


class UpdateSalesOrderStatus(StrEnum):
    DELIVERED = "DELIVERED"
    NOT_SHIPPED = "NOT_SHIPPED"
    PACKED = "PACKED"
    PENDING = "PENDING"

    def __str__(self) -> str:
        return str(self.value)
