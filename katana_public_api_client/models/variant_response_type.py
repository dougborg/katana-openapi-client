from enum import Enum


class VariantResponseType(str, Enum):
    MATERIAL = "material"
    PRODUCT = "product"
    SERVICE = "service"

    def __str__(self) -> str:
        return str(self.value)
