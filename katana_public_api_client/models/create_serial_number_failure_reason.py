from enum import StrEnum


class CreateSerialNumberFailureReason(StrEnum):
    DUPLICATE = "DUPLICATE"
    MISSING = "MISSING"

    def __str__(self) -> str:
        return str(self.value)
