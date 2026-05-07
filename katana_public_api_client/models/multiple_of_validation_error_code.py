from enum import StrEnum


class MultipleOfValidationErrorCode(StrEnum):
    MULTIPLEOF = "multipleOf"

    def __str__(self) -> str:
        return str(self.value)
