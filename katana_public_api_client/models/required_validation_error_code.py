from enum import Enum


class RequiredValidationErrorCode(str, Enum):
    REQUIRED = "required"

    def __str__(self) -> str:
        return str(self.value)
