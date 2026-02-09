from enum import StrEnum


class GetAllMaterialsExtendItem(StrEnum):
    SUPPLIER = "supplier"

    def __str__(self) -> str:
        return str(self.value)
