from enum import StrEnum


class StockTransferStatus(StrEnum):
    DRAFT = "draft"
    INTRANSIT = "inTransit"
    RECEIVED = "received"

    def __str__(self) -> str:
        return str(self.value)
