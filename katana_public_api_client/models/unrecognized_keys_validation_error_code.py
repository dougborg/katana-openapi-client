from enum import Enum


class UnrecognizedKeysValidationErrorCode(str, Enum):
    UNRECOGNIZED_KEYS = "unrecognized_keys"

    def __str__(self) -> str:
        return str(self.value)
