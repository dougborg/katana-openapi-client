from enum import StrEnum


class AdditionalPropertiesValidationErrorCode(StrEnum):
    ADDITIONALPROPERTIES = "additionalProperties"

    def __str__(self) -> str:
        return str(self.value)
