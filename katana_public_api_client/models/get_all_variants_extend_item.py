from enum import Enum


class GetAllVariantsExtendItem(str, Enum):
    PRODUCT_OR_MATERIAL = "product_or_material"

    def __str__(self) -> str:
        return str(self.value)
