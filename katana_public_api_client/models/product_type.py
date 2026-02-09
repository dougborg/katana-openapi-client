from enum import StrEnum


class ProductType(StrEnum):
    PRODUCT = "product"

    def __str__(self) -> str:
        return str(self.value)
