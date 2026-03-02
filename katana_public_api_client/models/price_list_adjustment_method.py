from enum import StrEnum


class PriceListAdjustmentMethod(StrEnum):
    FIXED = "fixed"
    MARKUP = "markup"
    PERCENTAGE = "percentage"

    def __str__(self) -> str:
        return str(self.value)
