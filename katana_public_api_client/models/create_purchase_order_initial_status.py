from enum import StrEnum


class CreatePurchaseOrderInitialStatus(StrEnum):
    NOT_RECEIVED = "NOT_RECEIVED"

    def __str__(self) -> str:
        return str(self.value)
