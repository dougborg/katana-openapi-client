from enum import StrEnum


class TooBigValidationErrorCode(StrEnum):
    TOO_BIG = "too_big"

    def __str__(self) -> str:
        return str(self.value)
