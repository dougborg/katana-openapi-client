from enum import StrEnum


class PatternValidationErrorCode(StrEnum):
    PATTERN = "pattern"

    def __str__(self) -> str:
        return str(self.value)
