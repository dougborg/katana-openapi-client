from enum import Enum


class UpdateStockTransferStatusRequestStatus(str, Enum):
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    IN_TRANSIT = "in_transit"
    PENDING = "pending"

    def __str__(self) -> str:
        return str(self.value)
