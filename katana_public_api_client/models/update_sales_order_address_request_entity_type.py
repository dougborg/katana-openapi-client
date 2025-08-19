from enum import Enum


class UpdateSalesOrderAddressRequestEntityType(str, Enum):
    BILLING = "billing"
    SHIPPING = "shipping"

    def __str__(self) -> str:
        return str(self.value)
