from enum import StrEnum


class MaxLengthValidationErrorCode(StrEnum):
    MAXLENGTH = "maxLength"

    def __str__(self) -> str:
        return str(self.value)
