from enum import StrEnum


class EnumValidationErrorCode(StrEnum):
    ENUM = "enum"

    def __str__(self) -> str:
        return str(self.value)
