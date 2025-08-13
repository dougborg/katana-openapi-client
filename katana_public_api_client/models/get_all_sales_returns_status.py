from enum import Enum


class GetAllSalesReturnsStatus(str, Enum):
    CANCELLED = "CANCELLED"
    DRAFT = "DRAFT"
    RETURNED = "RETURNED"

    def __str__(self) -> str:
        return str(self.value)
