from enum import Enum


class UpdateSalesOrderBodyStatus(str, Enum):
    DELIVERED = "DELIVERED"
    NOT_SHIPPED = "NOT_SHIPPED"
    PACKED = "PACKED"
    PENDING = "PENDING"

    def __str__(self) -> str:
        return str(self.value)
