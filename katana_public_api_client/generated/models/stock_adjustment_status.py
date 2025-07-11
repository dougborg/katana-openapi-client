from enum import Enum


class StockAdjustmentStatus(str, Enum):
    COMPLETED = "COMPLETED"
    DRAFT = "DRAFT"

    def __str__(self) -> str:
        return str(self.value)
