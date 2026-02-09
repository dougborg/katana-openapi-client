from enum import StrEnum


class GetMaterialExtendItem(StrEnum):
    SUPPLIER = "supplier"

    def __str__(self) -> str:
        return str(self.value)
