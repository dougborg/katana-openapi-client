from enum import Enum


class GetAllSerialNumbersStockStatus(str, Enum):
    IN_STOCK = "IN_STOCK"
    SOLD = "SOLD"
    TRANSFERRED = "TRANSFERRED"

    def __str__(self) -> str:
        return str(self.value)
