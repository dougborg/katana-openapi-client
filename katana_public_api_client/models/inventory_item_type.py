from enum import Enum


class InventoryItemType(str, Enum):
    MATERIAL = "material"
    PRODUCT = "product"

    def __str__(self) -> str:
        return str(self.value)
