from enum import Enum


class GetAllCustomerAddressesEntityType(str, Enum):
    OUTSOURCED = "outsourced"
    REGULAR = "regular"

    def __str__(self) -> str:
        return str(self.value)
