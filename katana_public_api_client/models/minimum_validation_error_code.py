from enum import StrEnum


class MinimumValidationErrorCode(StrEnum):
    MINIMUM = "minimum"

    def __str__(self) -> str:
        return str(self.value)
