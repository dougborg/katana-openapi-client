from enum import Enum


class GetAllManufacturingOrdersStatus(str, Enum):
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    NOT_STARTED = "NOT_STARTED"
    PAUSED = "PAUSED"

    def __str__(self) -> str:
        return str(self.value)
