from enum import Enum


class TooSmallValidationErrorCode(str, Enum):
    TOO_SMALL = "too_small"

    def __str__(self) -> str:
        return str(self.value)
