from enum import StrEnum


class InvalidTypeValidationErrorCode(StrEnum):
    INVALID_TYPE = "invalid_type"

    def __str__(self) -> str:
        return str(self.value)
