from enum import Enum


class EnumValidationErrorCode(str, Enum):
    ENUM = "enum"

    def __str__(self) -> str:
        return str(self.value)
