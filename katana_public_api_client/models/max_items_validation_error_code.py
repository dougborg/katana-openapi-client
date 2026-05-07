from enum import StrEnum


class MaxItemsValidationErrorCode(StrEnum):
    MAXITEMS = "maxItems"

    def __str__(self) -> str:
        return str(self.value)
