from enum import Enum


class MaxValidationErrorCode(str, Enum):
    MAX = "max"

    def __str__(self) -> str:
        return str(self.value)
