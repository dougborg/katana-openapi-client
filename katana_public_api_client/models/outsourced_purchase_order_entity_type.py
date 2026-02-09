from enum import StrEnum


class OutsourcedPurchaseOrderEntityType(StrEnum):
    OUTSOURCED = "outsourced"

    def __str__(self) -> str:
        return str(self.value)
