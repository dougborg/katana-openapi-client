from enum import Enum


class InvalidTypeValidationErrorCode(str, Enum):
    INVALID_TYPE = "invalid_type"

    def __str__(self) -> str:
        return str(self.value)
