from enum import Enum


class GetProductExtendItem(str, Enum):
    SUPPLIER = "supplier"

    def __str__(self) -> str:
        return str(self.value)
