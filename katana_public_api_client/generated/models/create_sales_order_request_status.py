from enum import Enum


class CreateSalesOrderRequestStatus(str, Enum):
    NOT_SHIPPED = "NOT_SHIPPED"
    PENDING = "PENDING"

    def __str__(self) -> str:
        return str(self.value)
