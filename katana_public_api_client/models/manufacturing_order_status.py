from enum import StrEnum


class ManufacturingOrderStatus(StrEnum):
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    IN_PROGRESS = "IN_PROGRESS"
    NOT_STARTED = "NOT_STARTED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"

    def __str__(self) -> str:
        return str(self.value)
