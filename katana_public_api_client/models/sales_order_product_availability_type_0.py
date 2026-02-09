from enum import StrEnum


class SalesOrderProductAvailabilityType0(StrEnum):
    EXPECTED = "EXPECTED"
    IN_STOCK = "IN_STOCK"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    PICKED = "PICKED"

    def __str__(self) -> str:
        return str(self.value)
