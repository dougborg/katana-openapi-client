from enum import StrEnum


class GetAllInventoryPointExtendItem(StrEnum):
    LOCATION = "location"
    VARIANT = "variant"

    def __str__(self) -> str:
        return str(self.value)
