from enum import StrEnum


class StockTransferStatus(StrEnum):
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    IN_TRANSIT = "in_transit"
    PENDING = "pending"

    def __str__(self) -> str:
        return str(self.value)
