from enum import StrEnum


class RegularPurchaseOrderEntityType(StrEnum):
    REGULAR = "regular"

    def __str__(self) -> str:
        return str(self.value)
