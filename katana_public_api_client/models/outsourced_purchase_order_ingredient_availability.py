from enum import Enum


class OutsourcedPurchaseOrderIngredientAvailability(str, Enum):
    EXPECTED = "EXPECTED"
    IN_STOCK = "IN_STOCK"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NO_RECIPE = "NO_RECIPE"
    PROCESSED = "PROCESSED"

    def __str__(self) -> str:
        return str(self.value)
