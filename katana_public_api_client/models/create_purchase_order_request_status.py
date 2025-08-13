from enum import Enum


class CreatePurchaseOrderRequestStatus(str, Enum):
    NOT_RECEIVED = "NOT_RECEIVED"

    def __str__(self) -> str:
        return str(self.value)
