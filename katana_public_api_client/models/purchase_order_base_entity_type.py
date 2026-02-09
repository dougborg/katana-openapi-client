from enum import StrEnum


class PurchaseOrderBaseEntityType(StrEnum):
    OUTSOURCED = "outsourced"
    REGULAR = "regular"

    def __str__(self) -> str:
        return str(self.value)
