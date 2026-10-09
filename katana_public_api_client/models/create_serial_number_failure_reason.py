from enum import StrEnum


class CreateSerialNumberFailureReason(StrEnum):
    DUPLICATE = "DUPLICATE"
    MISSING = "MISSING"
    NOT_IN_STOCK = "NOT_IN_STOCK"

    def __str__(self) -> str:
        return str(self.value)
