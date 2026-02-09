from enum import StrEnum


class CreatePurchaseOrderRequestStatus(StrEnum):
    NOT_RECEIVED = "NOT_RECEIVED"

    def __str__(self) -> str:
        return str(self.value)
