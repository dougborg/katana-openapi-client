from enum import StrEnum


class MinLengthValidationErrorCode(StrEnum):
    MINLENGTH = "minLength"

    def __str__(self) -> str:
        return str(self.value)
