from enum import StrEnum


class CreateSalesOrderRequestStatus(StrEnum):
    NOT_SHIPPED = "NOT_SHIPPED"
    PENDING = "PENDING"

    def __str__(self) -> str:
        return str(self.value)
