from enum import StrEnum


class CreateManufacturingOrderOperationRowRequestStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"

    def __str__(self) -> str:
        return str(self.value)
