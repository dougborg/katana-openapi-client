from enum import StrEnum


class InventoryItemType(StrEnum):
    MATERIAL = "material"
    PRODUCT = "product"

    def __str__(self) -> str:
        return str(self.value)
