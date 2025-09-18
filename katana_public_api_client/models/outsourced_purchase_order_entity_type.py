from enum import Enum


class OutsourcedPurchaseOrderEntityType(str, Enum):
    OUTSOURCED = "outsourced"

    def __str__(self) -> str:
        return str(self.value)
