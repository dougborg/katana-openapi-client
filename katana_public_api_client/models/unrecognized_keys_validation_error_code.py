from enum import StrEnum


class UnrecognizedKeysValidationErrorCode(StrEnum):
    UNRECOGNIZED_KEYS = "unrecognized_keys"

    def __str__(self) -> str:
        return str(self.value)
