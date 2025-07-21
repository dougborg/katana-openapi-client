from enum import Enum


class SalesOrderRowProductAvailabilityType0(str, Enum):
    EXPECTED = "EXPECTED"
    IN_STOCK = "IN_STOCK"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    PICKED = "PICKED"

    def __str__(self) -> str:
        return str(self.value)
