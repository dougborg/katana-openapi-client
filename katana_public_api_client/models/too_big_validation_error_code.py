from enum import Enum


class TooBigValidationErrorCode(str, Enum):
    TOO_BIG = "too_big"

    def __str__(self) -> str:
        return str(self.value)
