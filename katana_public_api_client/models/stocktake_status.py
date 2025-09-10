from enum import Enum


class StocktakeStatus(str, Enum):
    COMPLETED = "COMPLETED"
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    NOT_STARTED = "NOT_STARTED"

    def __str__(self) -> str:
        return str(self.value)
