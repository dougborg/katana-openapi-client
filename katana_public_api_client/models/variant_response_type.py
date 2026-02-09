from enum import StrEnum


class VariantResponseType(StrEnum):
    MATERIAL = "material"
    PRODUCT = "product"
    SERVICE = "service"

    def __str__(self) -> str:
        return str(self.value)
