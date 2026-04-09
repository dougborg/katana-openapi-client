from enum import StrEnum


class CreatePurchaseOrderInitialStatus(StrEnum):
    DRAFT = "DRAFT"
    NOT_RECEIVED = "NOT_RECEIVED"

    def __str__(self) -> str:
        return str(self.value)
