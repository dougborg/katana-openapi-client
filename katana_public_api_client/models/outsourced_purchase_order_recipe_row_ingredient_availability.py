from enum import Enum


class OutsourcedPurchaseOrderRecipeRowIngredientAvailability(str, Enum):
    EXPECTED = "EXPECTED"
    IN_STOCK = "IN_STOCK"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    PROCESSED = "PROCESSED"

    def __str__(self) -> str:
        return str(self.value)
