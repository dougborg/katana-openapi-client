from enum import Enum


class UpdateStocktakeRequestStatus(str, Enum):
    COMPLETED = "COMPLETED"
    COUNTED = "COUNTED"
    IN_PROGRESS = "IN_PROGRESS"
    NOT_STARTED = "NOT_STARTED"

    def __str__(self) -> str:
        return str(self.value)
