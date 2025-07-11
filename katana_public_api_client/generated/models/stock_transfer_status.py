from enum import Enum


class StockTransferStatus(str, Enum):
    COMPLETED = "COMPLETED"
    DRAFT = "DRAFT"

    def __str__(self) -> str:
        return str(self.value)
