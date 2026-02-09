from enum import StrEnum


class CustomerAddressEntityType(StrEnum):
    BILLING = "billing"
    SHIPPING = "shipping"

    def __str__(self) -> str:
        return str(self.value)
