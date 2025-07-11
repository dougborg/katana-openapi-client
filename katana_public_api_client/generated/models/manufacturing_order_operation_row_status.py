from enum import Enum


class ManufacturingOrderOperationRowStatus(str, Enum):
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"

    def __str__(self) -> str:
        return str(self.value)
