from enum import StrEnum


class ManufacturingOrderOperationRowStatus(StrEnum):
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    NOT_STARTED = "NOT_STARTED"
    PAUSED = "PAUSED"

    def __str__(self) -> str:
        return str(self.value)
