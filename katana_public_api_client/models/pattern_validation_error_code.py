from enum import Enum


class PatternValidationErrorCode(str, Enum):
    PATTERN = "pattern"

    def __str__(self) -> str:
        return str(self.value)
