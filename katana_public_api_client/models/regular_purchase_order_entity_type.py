from enum import Enum


class RegularPurchaseOrderEntityType(str, Enum):
    REGULAR = "regular"

    def __str__(self) -> str:
        return str(self.value)
