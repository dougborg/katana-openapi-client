from enum import StrEnum


class OneOfValidationErrorCode(StrEnum):
    ONEOF = "oneOf"

    def __str__(self) -> str:
        return str(self.value)
