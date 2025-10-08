from enum import Enum


class GetAllProductsExtendItem(str, Enum):
    SUPPLIER = "supplier"

    def __str__(self) -> str:
        return str(self.value)
