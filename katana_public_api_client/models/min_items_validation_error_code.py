from enum import StrEnum


class MinItemsValidationErrorCode(StrEnum):
    MINITEMS = "minItems"

    def __str__(self) -> str:
        return str(self.value)
