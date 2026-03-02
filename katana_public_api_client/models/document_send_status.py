from enum import StrEnum


class DocumentSendStatus(StrEnum):
    FAILED = "FAILED"
    NOT_SENT = "NOT_SENT"
    SENDING = "SENDING"
    SENT = "SENT"

    def __str__(self) -> str:
        return str(self.value)
