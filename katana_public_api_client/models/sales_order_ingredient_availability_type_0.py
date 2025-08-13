from enum import Enum


class SalesOrderIngredientAvailabilityType0(str, Enum):
    EXPECTED = "EXPECTED"
    IN_STOCK = "IN_STOCK"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NO_RECIPE = "NO_RECIPE"
    PROCESSED = "PROCESSED"

    def __str__(self) -> str:
        return str(self.value)
