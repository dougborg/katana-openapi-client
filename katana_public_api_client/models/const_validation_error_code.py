from enum import StrEnum


class ConstValidationErrorCode(StrEnum):
    CONST = "const"

    def __str__(self) -> str:
        return str(self.value)
