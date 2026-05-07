from enum import StrEnum


class TypeValidationErrorCode(StrEnum):
    TYPE = "type"

    def __str__(self) -> str:
        return str(self.value)
