from enum import StrEnum


class BinTransferStatus(StrEnum):
    CREATED = "CREATED"
    DONE = "DONE"
    IN_TRANSIT = "IN_TRANSIT"

    def __str__(self) -> str:
        return str(self.value)
