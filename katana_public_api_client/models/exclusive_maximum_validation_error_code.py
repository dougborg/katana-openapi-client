from enum import StrEnum


class ExclusiveMaximumValidationErrorCode(StrEnum):
    EXCLUSIVEMAXIMUM = "exclusiveMaximum"

    def __str__(self) -> str:
        return str(self.value)
