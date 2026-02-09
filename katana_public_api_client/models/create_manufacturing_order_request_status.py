from enum import StrEnum


class CreateManufacturingOrderRequestStatus(StrEnum):
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    IN_PROGRESS = "IN_PROGRESS"
    NOT_STARTED = "NOT_STARTED"

    def __str__(self) -> str:
        return str(self.value)
