from enum import StrEnum


class PurchaseOrderDocumentStatus(StrEnum):
    FAILED = "failed"
    NOTSENT = "notSent"
    SENDING = "sending"
    SENT = "sent"

    def __str__(self) -> str:
        return str(self.value)
