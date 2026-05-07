from enum import StrEnum


class ExclusiveMinimumValidationErrorCode(StrEnum):
    EXCLUSIVEMINIMUM = "exclusiveMinimum"

    def __str__(self) -> str:
        return str(self.value)
