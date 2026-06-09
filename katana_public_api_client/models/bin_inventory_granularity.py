from enum import StrEnum


class BinInventoryGranularity(StrEnum):
    BATCH = "BATCH"
    SERIAL_NUMBER = "SERIAL_NUMBER"
    VARIANT = "VARIANT"

    def __str__(self) -> str:
        return str(self.value)
