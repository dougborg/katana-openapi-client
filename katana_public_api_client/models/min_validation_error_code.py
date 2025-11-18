from enum import Enum


class MinValidationErrorCode(str, Enum):
    MIN = "min"

    def __str__(self) -> str:
        return str(self.value)
