from enum import StrEnum


class PriceAdjustmentMethod(StrEnum):
    FIXED = "fixed"
    MARKUP = "markup"
    PERCENTAGE = "percentage"

    def __str__(self) -> str:
        return str(self.value)
