from enum import StrEnum


class UniqueItemsValidationErrorCode(StrEnum):
    UNIQUEITEMS = "uniqueItems"

    def __str__(self) -> str:
        return str(self.value)
