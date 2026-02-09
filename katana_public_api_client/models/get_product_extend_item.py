from enum import StrEnum


class GetProductExtendItem(StrEnum):
    SUPPLIER = "supplier"

    def __str__(self) -> str:
        return str(self.value)
