from enum import Enum


class PurchaseOrderBaseLastDocumentStatus(str, Enum):
    FAILED = "FAILED"
    NOT_SENT = "NOT_SENT"
    SENDING = "SENDING"
    SENT = "SENT"

    def __str__(self) -> str:
        return str(self.value)
