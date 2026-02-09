from enum import StrEnum


class MinValidationErrorCode(StrEnum):
    MIN = "min"

    def __str__(self) -> str:
        return str(self.value)
