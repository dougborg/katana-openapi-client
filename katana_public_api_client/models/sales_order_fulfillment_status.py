from enum import Enum


class SalesOrderFulfillmentStatus(str, Enum):
    DELIVERED = "DELIVERED"
    PACKED = "PACKED"

    def __str__(self) -> str:
        return str(self.value)
