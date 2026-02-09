from enum import StrEnum


class MaxValidationErrorCode(StrEnum):
    MAX = "max"

    def __str__(self) -> str:
        return str(self.value)
