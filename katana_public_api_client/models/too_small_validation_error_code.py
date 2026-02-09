from enum import StrEnum


class TooSmallValidationErrorCode(StrEnum):
    TOO_SMALL = "too_small"

    def __str__(self) -> str:
        return str(self.value)
