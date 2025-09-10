from enum import Enum


class PriceListRowAdjustmentMethod(str, Enum):
    FIXED = "fixed"
    MARKUP = "markup"
    PERCENTAGE = "percentage"

    def __str__(self) -> str:
        return str(self.value)
