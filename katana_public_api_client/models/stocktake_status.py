from enum import StrEnum


class StocktakeStatus(StrEnum):
    COMPLETED = "COMPLETED"
    COUNTED = "COUNTED"
    IN_PROGRESS = "IN_PROGRESS"
    NOT_STARTED = "NOT_STARTED"

    def __str__(self) -> str:
        return str(self.value)
