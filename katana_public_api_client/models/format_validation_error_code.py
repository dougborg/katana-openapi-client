from enum import StrEnum


class FormatValidationErrorCode(StrEnum):
    FORMAT = "format"

    def __str__(self) -> str:
        return str(self.value)
