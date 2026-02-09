from enum import StrEnum


class CreateCustomerRequestAddressesItemEntityType(StrEnum):
    BILLING = "billing"
    SHIPPING = "shipping"

    def __str__(self) -> str:
        return str(self.value)
