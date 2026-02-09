from enum import StrEnum


class RequiredValidationErrorCode(StrEnum):
    REQUIRED = "required"

    def __str__(self) -> str:
        return str(self.value)
