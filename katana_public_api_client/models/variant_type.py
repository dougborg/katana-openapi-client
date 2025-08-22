from enum import Enum


class VariantType(str, Enum):
    MATERIAL = "material"
    PRODUCT = "product"

    def __str__(self) -> str:
        return str(self.value)
