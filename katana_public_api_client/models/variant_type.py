from enum import StrEnum


class VariantType(StrEnum):
    MATERIAL = "material"
    PRODUCT = "product"
    SERVICE = "service"

    def __str__(self) -> str:
        return str(self.value)
