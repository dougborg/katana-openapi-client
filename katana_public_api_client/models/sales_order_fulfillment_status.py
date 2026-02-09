from enum import StrEnum


class SalesOrderFulfillmentStatus(StrEnum):
    DELIVERED = "DELIVERED"
    PACKED = "PACKED"

    def __str__(self) -> str:
        return str(self.value)
