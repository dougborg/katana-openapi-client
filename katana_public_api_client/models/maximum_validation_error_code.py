from enum import StrEnum


class MaximumValidationErrorCode(StrEnum):
    MAXIMUM = "maximum"

    def __str__(self) -> str:
        return str(self.value)
